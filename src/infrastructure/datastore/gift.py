import logging
import asyncio
from google.cloud import datastore
from models.gift import Gift, GiftType
from infrastructure.datastore.base import DatastoreRepository

logger = logging.getLogger(__name__)


class GiftDatastoreRepository(DatastoreRepository[Gift]):
    def __init__(self):
        super().__init__(Gift.kind)

    def _entity_to_domain(self, entity: datastore.Entity) -> Gift:
        entity_id = None
        if entity.key and entity.key.id:
            entity_id = entity.key.id

        return Gift(
            id=entity_id,
            sender_id=entity["sender_id"],
            sender_name=entity["sender_name"],
            receiver_id=entity["receiver_id"],
            gift_type=GiftType(entity["gift_type"]),
            created_at=entity["created_at"],
            cost=entity.get("cost", 0),
        )

    async def get_gifts_for_user(self, user_id: int) -> list[Gift]:
        def _fetch():
            query = self.client.query(kind=self.kind)
            query.add_filter("receiver_id", "=", user_id)
            results = [self._entity_to_domain(entity) for entity in query.fetch()]
            # Sort in memory to avoid needing a composite index
            results.sort(key=lambda x: x.created_at, reverse=True)
            return results

        return await asyncio.to_thread(_fetch)


gift_repository = GiftDatastoreRepository()
