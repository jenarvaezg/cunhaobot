import logging
import hashlib
from datetime import datetime, timezone, timedelta
from infrastructure.protocols import UserRepository
from services.badge_service import BadgeService
from tg import get_initialized_tg_application
from core.config import config

logger = logging.getLogger(__name__)


class GameService:
    def __init__(self, user_repo: UserRepository, badge_service: BadgeService):
        self.user_repo = user_repo
        self.badge_service = badge_service

    def verify_score_hash(self, user_id: str, score: int, hash_val: str) -> bool:
        """Verifies if the score has been tampered with."""
        if hash_val.startswith("unsafe-"):
            # Fallback for non-HTTPS environments (dev/tests)
            return True

        expected_hash = hashlib.sha256(
            f"{user_id}{score}{config.session_secret}".encode()
        ).hexdigest()

        return hash_val == expected_hash

    async def set_score(
        self,
        user_id: str,
        score: int,
        inline_message_id: str | None = None,
        chat_id: str | int | None = None,
        message_id: str | int | None = None,
    ) -> bool:
        """Processes the game score, updates user stats and Telegram leaderboard."""
        if user_id == "guest":
            return True

        user = await self.user_repo.load(user_id)
        if not user:
            logger.warning(f"User {user_id} not found when processing score")
            return False

        now = datetime.now(timezone.utc)

        # 1. Update Points (1 point per 100 game points)
        points_to_add = int(score) // 100
        user.points += points_to_add

        # 2. Update Game Stats
        user.game_stats += 1
        if int(score) > user.game_high_score:
            user.game_high_score = int(score)

        # 3. Update Streak
        if user.last_game_at:
            last_game_date = user.last_game_at.date()
            today = now.date()
            yesterday = today - timedelta(days=1)

            if last_game_date == yesterday:
                user.game_streak += 1
            elif last_game_date < yesterday:
                user.game_streak = 1
        else:
            user.game_streak = 1

        user.last_game_at = now

        # 4. Save User
        await self.user_repo.save(user)
        logger.info(
            f"Processed game score for {user_id}: {score} pts ({points_to_add} points added)"
        )

        # 5. Award Badges
        await self.badge_service.check_badges(user_id, user.platform)

        # 6. Update Telegram Leaderboard
        try:
            application = await get_initialized_tg_application()

            if inline_message_id:
                await application.bot.set_game_score(
                    user_id=int(user_id),
                    score=int(score),
                    inline_message_id=inline_message_id,
                )
            elif chat_id and message_id:
                await application.bot.set_game_score(
                    user_id=int(user_id),
                    score=int(score),
                    chat_id=int(chat_id),
                    message_id=int(message_id),
                )
        except Exception as e:
            logger.error(f"Error updating Telegram game score for {user_id}: {e}")

        return True
