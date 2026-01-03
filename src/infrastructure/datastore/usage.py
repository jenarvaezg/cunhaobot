import asyncio
import logging
from google.cloud import datastore
from models.usage import UsageRecord
from infrastructure.datastore.base import DatastoreRepository

logger = logging.getLogger(__name__)


class UsageDatastoreRepository(DatastoreRepository[UsageRecord]):
    def __init__(self):
        super().__init__("Usage")

    def _entity_to_domain(self, entity: datastore.Entity) -> UsageRecord:
        return UsageRecord(
            user_id=entity["user_id"],
            platform=entity["platform"],
            action=entity["action"],
            phrase_id=entity.get("phrase_id"),
            timestamp=entity["timestamp"],
            metadata=entity.get("metadata", {}),
        )

    async def get_user_usage_count(
        self, user_id: str, platform: str | None = None
    ) -> int:
        def _count():
            try:
                query = self.client.query(kind=self.kind)
                query.add_filter("user_id", "=", user_id)
                if platform:
                    query.add_filter("platform", "=", platform)

                count_query = self.client.aggregation_query(query=query)
                count_query.count(alias="all")
                results = list(count_query.fetch())
                if results and len(results) > 0 and len(results[0]) > 0:
                    return int(results[0][0].value)
                return 0
            except Exception as e:
                logger.error(f"Error counting usage for {user_id}: {e}")
                return 0

        return await asyncio.to_thread(_count)

    async def get_user_action_count(self, user_id: str, action: str) -> int:
        """Counts how many times a user has performed a specific action."""

        def _count():
            try:
                query = self.client.query(kind=self.kind)
                query.add_filter("user_id", "=", str(user_id))
                query.add_filter("action", "=", action)

                count_query = self.client.aggregation_query(query=query)
                count_query.count(alias="all")
                results = list(count_query.fetch())
                if results and len(results) > 0 and len(results[0]) > 0:
                    return int(results[0][0].value)
                return 0
            except Exception as e:
                logger.error(f"Error counting action {action} for {user_id}: {e}")
                return 0

        return await asyncio.to_thread(_count)


usage_repository = UsageDatastoreRepository()
