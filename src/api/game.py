import logging
import hashlib
import zlib
from typing import Annotated
from litestar import Controller, Request, get, post
from litestar.response import Template
from litestar.params import Dependency
from litestar.exceptions import HTTPException

from services.game_service import GameService
from services.user_service import UserService
from services.tts_service import TTSService
from services.phrase_service import PhraseService
from core.config import config
from utils.ui import apelativo
from models.phrase import Phrase

logger = logging.getLogger(__name__)


class GameController(Controller):
    path = "/game"

    @get("/launch")
    async def launch_game(
        self,
        request: Request,
        tts_service: Annotated[TTSService, Dependency()],
        phrase_service: Annotated[PhraseService, Dependency()],
    ) -> Template:
        """Endpoint called by Telegram to launch the game."""
        # Validate telegram web app init data if possible, or use simplified launch
        tg_data = dict(request.query_params)
        user_id = tg_data.get("user_id")
        inline_message_id = tg_data.get("inline_message_id")
        chat_id = tg_data.get("chat_id")
        message_id = tg_data.get("message_id")

        if not user_id:
            # Fallback for testing or direct access
            user_id = "guest"

        # Generate greeting audio
        ap = apelativo()
        text = f"¿Qué pasa, {ap}?"
        # Use a stable integer ID for caching based on the apelativo
        phrase_id = zlib.adler32(text.encode())
        dummy_phrase = Phrase(text=text, id=phrase_id)

        # Use "short" to match telegram audio mode prefixing
        greeting_audio_url = tts_service.get_audio_url(dummy_phrase, "short")

        # Generate Game Over audio (random long phrase)
        random_phrase = await phrase_service.get_random(long=True)
        if random_phrase.id is None:
            random_phrase.id = zlib.adler32(random_phrase.text.encode())

        game_over_audio_url = tts_service.get_audio_url(random_phrase, "long")

        return Template(
            template_name="game.html",
            context={
                "user_id": user_id,
                "inline_message_id": inline_message_id,
                "chat_id": chat_id,
                "message_id": message_id,
                "game_short_name": "palillo_cunhao",
                "secret": config.session_secret,
                "is_web": False,
                "greeting_audio_url": greeting_audio_url,
                "game_over_audio_url": game_over_audio_url,
            },
        )

    @get("/ranking")
    async def game_ranking(
        self,
        request: Request,
        user_service: Annotated[UserService, Dependency()],
    ) -> Template:
        """Renders the global game ranking."""
        # Load all users and sort by game_high_score
        users = await user_service.user_repo.load_all()
        ranking = sorted(
            [u for u in users if u.game_high_score > 0],
            key=lambda x: x.game_high_score,
            reverse=True,
        )[:50]

        return Template(
            template_name="game_ranking.html",
            context={
                "ranking": ranking,
                "game_short_name": "palillo_cunhao",
            },
        )

    @post("/score")
    async def submit_score(
        self,
        request: Request,
        game_service: Annotated[GameService, Dependency()],
        user_service: Annotated[UserService, Dependency()],
    ) -> dict[str, str | bool]:
        """Submit score from the game."""
        data = await request.json()
        user_id = data.get("user_id")
        score = data.get("score", 0)
        inline_message_id = data.get("inline_message_id") or None
        chat_id = data.get("chat_id") or None
        message_id = data.get("message_id") or None
        hash_received = data.get("hash")

        # Verify hash to prevent cheating
        # hash = sha256(user_id + score + secret)
        data_to_hash = f"{user_id}{score}{config.session_secret}"
        expected_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()

        if hash_received != expected_hash:
            logger.warning(f"Invalid score hash for user {user_id}")
            raise HTTPException(status_code=403, detail="Invalid score verification")

        # Save score and update highscore in Telegram
        success = await game_service.set_score(
            user_id=user_id,
            score=score,
            inline_message_id=inline_message_id,
            chat_id=chat_id,
            message_id=message_id,
        )

        # If it failed, maybe user is missing from DB (e.g. web play without prior bot interaction)
        if not success and user_id != "guest":
            user_session = request.session.get("user")
            if user_session and str(user_session.get("id")) == str(user_id):
                # Create skeleton user from session
                await user_service.update_user_data(
                    user_id=user_id,
                    name=user_session.get("first_name", "Usuario Web"),
                    username=user_session.get("username"),
                )
                # Retry
                success = await game_service.set_score(
                    user_id=user_id,
                    score=score,
                    inline_message_id=inline_message_id,
                    chat_id=chat_id,
                    message_id=message_id,
                )

        # Award points to user based on performance (1 point per 100 points in game)
        if success and user_id != "guest":
            points = int(score / 100)
            if points > 0:
                await user_service.add_points(user_id, points)

        return {"status": "ok", "success": success}
