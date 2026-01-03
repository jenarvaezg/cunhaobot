import asyncio
import logging
from typing import Generic, TypeVar
from google.cloud import datastore
from pydantic import BaseModel
from utils.gcp import get_datastore_client

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class DatastoreRepository(Generic[T]):
    def __init__(self, kind: str):
        self.kind = kind
        self._cache: list[T] = []

    @property
    def client(self) -> datastore.Client:
        return get_datastore_client()

    def get_key(self, entity_id: str | int) -> datastore.Key:
        return self.client.key(self.kind, entity_id)

    async def delete(self, entity_id: str | int) -> None:
        def _delete():
            self.client.delete(self.get_key(entity_id))

        await asyncio.to_thread(_delete)
        self.clear_cache()

    def clear_cache(self) -> None:
        self._cache = []

    def _entity_to_domain(self, entity: datastore.Entity) -> T:
        """Must be implemented by subclasses."""
        raise NotImplementedError

    def _domain_to_entity(self, model: T, key: datastore.Key) -> datastore.Entity:
        """Default implementation using model_dump."""
        entity = datastore.Entity(key=key)
        entity.update(model.model_dump())
        return entity

    async def load(self, entity_id: str | int) -> T | None:
        def _get():
            key = self.get_key(entity_id)
            entity = self.client.get(key)
            return self._entity_to_domain(entity) if entity else None

        return await asyncio.to_thread(_get)

    async def load_all(self) -> list[T]:
        if not self._cache:

            def _fetch():
                query = self.client.query(kind=self.kind)
                return [self._entity_to_domain(entity) for entity in query.fetch()]

            self._cache = await asyncio.to_thread(_fetch)
        return self._cache

    async def save(self, model: T) -> None:
        # Pydantic models might have an 'id' attribute
        entity_id = getattr(model, "id", None)

        def _put():
            if entity_id:
                key = self.get_key(entity_id)
            else:
                key = self.client.key(self.kind)

            entity = self._domain_to_entity(model, key)
            self.client.put(entity)

            # If it was a new entity, update the model ID if possible
            if not entity_id and entity.key and entity.key.id:
                if hasattr(model, "id"):
                    setattr(model, "id", entity.key.id)

        await asyncio.to_thread(_put)
        self.clear_cache()
