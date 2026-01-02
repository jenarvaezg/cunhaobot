import logging
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from models.usage import UsageRecord, ActionType
from infrastructure.datastore.usage import usage_repository

if TYPE_CHECKING:
    from services.badge_service import Badge

logger = logging.getLogger(__name__)


class UsageService:
    def __init__(self, repo=usage_repository):
        self.repo = repo

    async def log_usage(
        self,
        user_id: str | int,
        platform: str,
        action: ActionType,
        phrase_id: str | int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list["Badge"]:
        try:
            from services.user_service import user_service

            # Ensure we use the master user ID for logging if linked
            master_user = user_service.get_user(user_id, platform)
            effective_user_id = str(master_user.id) if master_user else str(user_id)
            # We keep the original platform for the record to know where it came from

            record = UsageRecord(
                user_id=effective_user_id,
                platform=platform,
                action=action,
                phrase_id=str(phrase_id) if phrase_id else None,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {},
            )
            self.repo.save(record)
            logger.debug(
                f"Logged usage: {action} for user {effective_user_id} (orig: {user_id}) on {platform}"
            )

            from services.badge_service import badge_service

            return await badge_service.check_badges(effective_user_id, platform)
        except Exception as e:
            logger.error(f"Error logging usage: {e}")
            return []

    def get_user_stats(
        self, user_id: str | int, platform: str | None = None
    ) -> dict[str, int]:
        # If platform is provided, it will still filter, but we might want global count
        # For unified profile, we call it without platform
        count = self.repo.get_user_usage_count(str(user_id), platform)
        return {
            "total_usages": count,
        }


usage_service = UsageService()
