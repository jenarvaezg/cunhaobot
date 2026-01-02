from google.cloud import datastore
from models.usage import UsageRecord
from infrastructure.datastore.base import DatastoreRepository


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

    def _domain_to_entity(
        self, record: UsageRecord, key: datastore.Key
    ) -> datastore.Entity:
        entity = datastore.Entity(key=key)
        # Convert timestamp to something Datastore likes if needed,
        # but datastore client usually handles datetime objects fine.
        entity.update(record.model_dump())
        return entity

    def save(self, record: UsageRecord) -> None:
        key = self.client.key(self.kind)
        entity = self._domain_to_entity(record, key)
        self.client.put(entity)

    def get_user_usage_count(self, user_id: str, platform: str | None = None) -> int:
        try:
            query = self.client.query(kind=self.kind)
            query.add_filter("user_id", "=", user_id)
            if platform:
                query.add_filter("platform", "=", platform)
            query.keys_only()
            return len(list(query.fetch(limit=5000)))  # Limit to 5000 to avoid timeouts
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Error counting usage for {user_id}: {e}"
            )
            return 0

    def get_user_action_count(
        self, user_id: str, platform: str | None = None, action: str | None = None
    ) -> int:
        """Counts how many times a user has performed a specific action."""
        try:
            query = self.client.query(kind=self.kind)
            query.add_filter("user_id", "=", str(user_id))
            if platform:
                query.add_filter("platform", "=", platform)
            if action:
                query.add_filter("action", "=", action)
            query.keys_only()
            return len(list(query.fetch(limit=5000)))
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Error counting action {action} for {user_id}: {e}"
            )
            return 0


usage_repository = UsageDatastoreRepository()
