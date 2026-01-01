import logging
from datetime import datetime
from typing import Any

from models.usage import UsageRecord, ActionType
from infrastructure.datastore.usage import usage_repository


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
    ) -> list[Any]:
        try:
            record = UsageRecord(
                user_id=str(user_id),
                platform=platform,
                action=action,
                phrase_id=str(phrase_id) if phrase_id else None,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )
            self.repo.save(record)
            logger.debug(f"Logged usage: {action} for user {user_id} on {platform}")

            from services.badge_service import badge_service

            return await badge_service.check_badges(user_id, platform)
        except Exception as e:
            logger.error(f"Error logging usage: {e}")
            return []

    def get_user_stats(self, user_id: str | int, platform: str) -> dict[str, Any]:
        count = self.repo.get_user_usage_count(str(user_id), platform)
        return {
            "total_usages": count,
        }


usage_service = UsageService()
