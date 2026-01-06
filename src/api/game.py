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

        if not user_id:
            # Fallback for testing or direct access
            user_id = "guest"

        # Generate greeting audio
        ap = apelativo()
        text = f"¿Qué pasa, {ap}?"
        # Use a stable integer ID for caching based on the apelativo
        phrase_id = zlib.adler32(text.encode())
        dummy_phrase = Phrase(text=text, id=phrase_id)

        greeting_audio_url = tts_service.get_audio_url(dummy_phrase, "game")

        # Generate Game Over audio (random long phrase)
        random_phrase = await phrase_service.get_random(long=True)
        game_over_audio_url = tts_service.get_audio_url(random_phrase, "long")

        return Template(
            template_name="game.html",
            context={
                "user_id": user_id,
                "inline_message_id": inline_message_id,
                "game_short_name": "palillo_cunhao",
                "secret": config.session_secret,
                "is_web": False,
                "greeting_audio_url": greeting_audio_url,
                "game_over_audio_url": game_over_audio_url,
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
        inline_message_id = data.get("inline_message_id")
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
        )

        # Award points to user based on performance (1 point per 100 points in game)
        if success and user_id != "guest":
            points = int(score / 100)
            if points > 0:
                await user_service.add_points(user_id, points)

        return {"status": "ok", "success": success}
