from google.cloud import datastore
from models.link_request import LinkRequest
from infrastructure.datastore.base import DatastoreRepository


class LinkRequestRepository(DatastoreRepository[LinkRequest]):
    def __init__(self):
        super().__init__("LinkRequest")

    def _entity_to_domain(self, entity: datastore.Entity) -> LinkRequest:
        return LinkRequest(
            token=entity.key.name,
            source_user_id=entity["source_user_id"],
            source_platform=entity["source_platform"],
            created_at=entity["created_at"],
            expires_at=entity["expires_at"],
        )

    def _domain_to_entity(
        self, record: LinkRequest, key: datastore.Key
    ) -> datastore.Entity:
        entity = datastore.Entity(key=key)
        entity.update(
            {
                "source_user_id": record.source_user_id,
                "source_platform": record.source_platform,
                "created_at": record.created_at,
                "expires_at": record.expires_at,
            }
        )
        return entity

    def save(self, record: LinkRequest) -> None:
        key = self.client.key(self.kind, record.token)
        entity = self._domain_to_entity(record, key)
        self.client.put(entity)

    def load(self, token: str) -> LinkRequest | None:
        key = self.client.key(self.kind, token)
        entity = self.client.get(key)
        if entity:
            return self._entity_to_domain(entity)
        return None

    def delete(self, entity_id: str | int) -> None:
        key = self.client.key(self.kind, str(entity_id))
        self.client.delete(key)


link_request_repository = LinkRequestRepository()
