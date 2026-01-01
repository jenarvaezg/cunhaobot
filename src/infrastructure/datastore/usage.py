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

    def get_user_usage_count(self, user_id: str, platform: str) -> int:
        query = self.client.query(kind=self.kind)
        query.add_filter("user_id", "=", user_id)
        query.add_filter("platform", "=", platform)
        return len(list(query.fetch()))


usage_repository = UsageDatastoreRepository()
