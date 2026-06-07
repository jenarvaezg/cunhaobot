import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from infrastructure.protocols import UserRepository
from models.user import User
from services.badge_service import BadgeService
from core.config import config

logger = logging.getLogger(__name__)


class InvalidGameSessionError(Exception):
    """Raised when a game score is submitted outside a valid game session."""


class GamePlayerProfile(BaseModel):
    user_id: str | int
    name: str = "Usuario Web"
    username: str | None = None
    platform: str = "telegram"


class GameService:
    def __init__(self, user_repo: UserRepository, badge_service: BadgeService):
        self.user_repo = user_repo
        self.badge_service = badge_service

    def generate_game_token(self, user_id: str | int) -> str:
        timestamp = int(time.time())
        payload = f"{user_id}:{timestamp}"
        signature = hmac.new(
            config.session_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return f"{signature}:{timestamp}"

    def verify_game_token(self, user_id: str | int, token: str) -> bool:
        try:
            signature, timestamp_str = token.split(":")
            timestamp = int(timestamp_str)
        except (ValueError, AttributeError):
            return False

        if time.time() - timestamp > 7200:
            return False

        payload = f"{user_id}:{timestamp}"
        expected_signature = hmac.new(
            config.session_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)

    async def submit_score(
        self,
        user_id: str | int,
        score: int,
        token: str,
        inline_message_id: str | None = None,
        chat_id: str | int | None = None,
        message_id: str | int | None = None,
        player_profile: GamePlayerProfile | None = None,
    ) -> bool:
        if not self.verify_game_token(user_id, token):
            raise InvalidGameSessionError

        success = await self.set_score(
            user_id=str(user_id),
            score=score,
            inline_message_id=inline_message_id,
            chat_id=chat_id,
            message_id=message_id,
        )
        if success or user_id == "guest":
            return success

        if player_profile is None or str(player_profile.user_id) != str(user_id):
            return False

        await self._ensure_player_profile(player_profile)
        return await self.set_score(
            user_id=str(user_id),
            score=score,
            inline_message_id=inline_message_id,
            chat_id=chat_id,
            message_id=message_id,
        )

    async def _ensure_player_profile(self, profile: GamePlayerProfile) -> None:
        uid_to_load = profile.user_id
        if isinstance(profile.user_id, str) and profile.user_id.lstrip("-").isdigit():
            uid_to_load = int(profile.user_id)

        user = await self.user_repo.load(uid_to_load)
        if not user and isinstance(uid_to_load, int):
            user = await self.user_repo.load(str(uid_to_load))

        if not user:
            await self.user_repo.save(
                User(
                    id=profile.user_id,
                    name=profile.name,
                    username=profile.username,
                    platform=profile.platform,
                )
            )
            return

        changed = False
        if user.name != profile.name:
            user.name = profile.name
            changed = True
        if user.username != profile.username:
            user.username = profile.username
            changed = True
        if user.platform != profile.platform and str(user.id) == str(profile.user_id):
            user.platform = profile.platform
            changed = True

        if changed:
            await self.user_repo.save(user)

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

        # Ensure user_id is int if it looks like one (Telegram IDs are ints)
        uid_to_load = user_id
        if isinstance(user_id, str) and user_id.lstrip("-").isdigit():
            uid_to_load = int(user_id)

        user = await self.user_repo.load(uid_to_load)
        if not user:
            # Fallback: try as string if int failed (legacy support?)
            if isinstance(uid_to_load, int):
                user = await self.user_repo.load(str(uid_to_load))

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
        new_badges = await self.badge_service.check_badges(user_id, user.platform)
        if new_badges:
            try:
                from utils.ui import format_badge_notification
                import telegram
                from tg import get_initialized_tg_application

                application = await get_initialized_tg_application()
                for badge in new_badges:
                    text = await format_badge_notification(badge)
                    await application.bot.send_message(
                        chat_id=int(user_id),
                        text=text,
                        parse_mode=telegram.constants.ParseMode.HTML,
                    )
            except Exception as e:
                logger.error(f"Error notifying game badges for {user_id}: {e}")

        # 6. Update Telegram Leaderboard
        try:
            from tg import get_initialized_tg_application

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
