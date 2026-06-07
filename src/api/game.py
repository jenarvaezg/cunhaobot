import logging
import zlib
from collections.abc import Mapping
from typing import Annotated, cast
from litestar import Controller, Request, get, post
from litestar.response import Template
from litestar.params import Dependency
from litestar.exceptions import HTTPException

from services.game_service import (
    GamePlayerProfile,
    GameService,
    InvalidGameSessionError,
)
from services.user_service import UserService
from services.tts_service import TTSService
from services.phrase_service import PhraseService
from utils.ui import apelativo
from models.phrase import Phrase

logger = logging.getLogger(__name__)


def _player_profile_from_session(session_user: object) -> GamePlayerProfile | None:
    if not isinstance(session_user, Mapping):
        return None

    session_data = cast(Mapping[str, object], session_user)
    user_id = session_data.get("id")
    if not isinstance(user_id, str | int):
        return None

    first_name = session_data.get("first_name")
    username = session_data.get("username")
    name = first_name if isinstance(first_name, str) and first_name else "Usuario Web"
    return GamePlayerProfile(
        user_id=user_id,
        name=name,
        username=username if isinstance(username, str) else None,
    )


class GameController(Controller):
    path = "/game"

    @get("/launch")
    async def launch_game(
        self,
        request: Request,
        tts_service: Annotated[TTSService, Dependency()],
        phrase_service: Annotated[PhraseService, Dependency()],
        user_service: Annotated[UserService, Dependency()],
        game_service: Annotated[GameService, Dependency()],
    ) -> Template:
        """Endpoint called by Telegram to launch the game."""
        # Validate telegram web app init data if possible, or use simplified launch
        tg_data = dict(request.query_params)
        user_id = tg_data.get("user_id")
        inline_message_id = tg_data.get("inline_message_id")
        chat_id = tg_data.get("chat_id")
        message_id = tg_data.get("message_id")
        user_name = tg_data.get("name")
        username = tg_data.get("username")

        high_score = 0
        if not user_id:
            # Fallback for testing or direct access
            user_id = "guest"
        else:
            # Ensure user exists in DB so ranking works for new web players
            if user_name:
                user = await user_service.update_user_data(
                    user_id=user_id,
                    name=user_name,
                    username=username,
                )
            else:
                user = await user_service.get_user(user_id)

            if user:
                high_score = user.game_high_score

        # Daily Challenge Logic: Select an item based on the day of the year
        import datetime

        day_of_year = datetime.datetime.now().timetuple().tm_yday
        challenges = [
            {"type": "croqueta", "name": "Croqueta", "multiplier": 2},
            {"type": "jamon", "name": "Jamón", "multiplier": 2},
            {
                "type": "aguacate",
                "name": "Aguacate",
                "multiplier": 0,
            },  # Sushi/Aguacate give points instead of damage
            {"type": "sushi", "name": "Sushi", "multiplier": 0},
            {
                "type": "factura",
                "name": "La Cuenta",
                "multiplier": -0.5,
            },  # Factura only hurts half
        ]
        daily_challenge = challenges[day_of_year % len(challenges)]

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

        import json

        return Template(
            template_name="game.html",
            context={
                "user_id": user_id,
                "inline_message_id": inline_message_id,
                "chat_id": chat_id,
                "message_id": message_id,
                "game_short_name": "palillo_cunhao",
                "game_token": game_service.generate_game_token(user_id),
                "is_web": False,
                "greeting_audio_url": greeting_audio_url,
                "game_over_audio_url": game_over_audio_url,
                "daily_challenge_json": json.dumps(daily_challenge),
                "high_score": high_score,
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
        user_service.user_repo.clear_cache()
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
    ) -> dict[str, str | bool]:
        """Submit score from the game."""
        data = await request.json()
        user_id = data.get("user_id")
        score = int(data.get("score", 0))
        inline_message_id = data.get("inline_message_id") or None
        chat_id = data.get("chat_id") or None
        message_id = data.get("message_id") or None
        token = data.get("token")

        if not isinstance(user_id, str | int) or not isinstance(token, str):
            logger.warning(f"Invalid game token for user {user_id}")
            raise HTTPException(status_code=403, detail="Invalid game session")

        try:
            success = await game_service.submit_score(
                user_id=user_id,
                score=score,
                token=token,
                inline_message_id=inline_message_id,
                chat_id=chat_id,
                message_id=message_id,
                player_profile=_player_profile_from_session(
                    request.session.get("user")
                ),
            )
        except InvalidGameSessionError:
            logger.warning(f"Invalid game token for user {user_id}")
            raise HTTPException(
                status_code=403, detail="Invalid game session"
            ) from None

        return {"status": "ok", "success": success}
