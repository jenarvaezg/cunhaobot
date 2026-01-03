from typing import cast
from google.cloud import datastore
from models.link_request import LinkRequest
from infrastructure.datastore.base import DatastoreRepository


class LinkRequestRepository(DatastoreRepository[LinkRequest]):
    def __init__(self):
        super().__init__("LinkRequest")

    def _entity_to_domain(self, entity: datastore.Entity) -> LinkRequest:
        key = cast(datastore.Key, entity.key)
        token = cast(str | None, key.name)
        if not token:
            raise ValueError("Entity key name is missing")
        return LinkRequest(
            token=token,
            source_user_id=entity["source_user_id"],
            source_platform=entity["source_platform"],
            created_at=entity["created_at"],
            expires_at=entity["expires_at"],
        )

    def _domain_to_entity(
        self, model: LinkRequest, key: datastore.Key
    ) -> datastore.Entity:
        entity = datastore.Entity(key=key)
        entity.update(
            {
                "source_user_id": model.source_user_id,
                "source_platform": model.source_platform,
                "created_at": model.created_at,
                "expires_at": model.expires_at,
            }
        )
        return entity


link_request_repository = LinkRequestRepository()
