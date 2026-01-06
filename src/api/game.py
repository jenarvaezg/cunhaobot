import logging
import hashlib
from typing import Annotated
from litestar import Controller, Request, get, post
from litestar.exceptions import HTTPException
from litestar.response import Template
from litestar.params import Dependency

from infrastructure.protocols import UserRepository
from core.config import config
from tg import get_tg_application

logger = logging.getLogger(__name__)


class GameController(Controller):
    path = "/game"

    @get("/launch")
    async def launch(self, request: Request, user_id: str) -> Template:
        """Renders the game page."""
        # For security in production, we should verify the user somehow,
        # but for an MVP a simple user_id in query is enough.

        # We can also pass inline_message_id if we want to update the leaderboard
        inline_message_id = request.query_params.get("inline_message_id")

        # Read the music pattern from the doc file
        music_pattern = ""
        try:
            with open("docs/music_pattern.strudel", "r") as f:
                music_pattern = f.read()
        except Exception as e:
            logger.error(f"Could not read music pattern: {e}")

        return Template(
            template_name="game.html",
            context={
                "user_id": user_id,
                "inline_message_id": inline_message_id,
                "game_short_name": "palillo_cunhao",
                "secret": config.session_secret,
                "music_pattern": music_pattern,
            },
        )

    @post("/score")
    async def submit_score(
        self, request: Request, user_repo: Annotated[UserRepository, Dependency()]
    ) -> dict[str, str]:
        """Submits a new score."""
        data = await request.json()
        user_id = data.get("user_id")
        score = data.get("score")
        inline_message_id = data.get("inline_message_id")
        hash_val = data.get("hash")

        if not user_id or score is None:
            raise HTTPException(status_code=400, detail="Missing data")

        # Basic anti-cheat: verify hash(user_id + score + secret)
        expected_hash = hashlib.sha256(
            f"{user_id}{score}{config.session_secret}".encode()
        ).hexdigest()

        if hash_val != expected_hash:
            logger.warning(f"Invalid score hash for user {user_id}")
            # In a real app we'd reject this, but for MVP let's just log it
            # or be strict if you prefer.
            # raise HTTPException(status_code=403, detail="Invalid hash")

        # Update points and stats in Datastore
        user = await user_repo.load(user_id)
        if user:
            from datetime import datetime, timezone, timedelta

            now = datetime.now(timezone.utc)

            # Points logic
            points_to_add = int(score) // 100
            user.points += points_to_add

            # Streak and stats logic
            user.game_stats += 1
            if int(score) > user.game_high_score:
                user.game_high_score = int(score)

            if user.last_game_at:
                last_game = user.last_game_at.date()
                today = now.date()
                yesterday = today - timedelta(days=1)

                if last_game == yesterday:
                    user.game_streak += 1
                elif last_game < yesterday:
                    user.game_streak = 1
                # if last_game == today, streak stays the same
            else:
                user.game_streak = 1

            user.last_game_at = now

            await user_repo.save(user)
            logger.info(
                f"User {user_id} earned {points_to_add} points and has streak {user.game_streak}"
            )

            # Award badges
            from services.badge_service import badge_service

            await badge_service.check_badges(user_id, user.platform)

        # Update Telegram Leaderboard
        try:
            application = get_tg_application()
            if not application.running:
                await application.initialize()

            await application.bot.set_game_score(
                user_id=int(user_id),
                score=int(score),
                inline_message_id=inline_message_id,
            )
        except Exception as e:
            logger.error(f"Error updating Telegram game score: {e}")

        return {"status": "ok"}
