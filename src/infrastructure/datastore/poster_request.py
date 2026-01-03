import asyncio
from models.poster_request import PosterRequest
from infrastructure.datastore.base import DatastoreRepository


class PosterRequestRepository(DatastoreRepository[PosterRequest]):
    def __init__(self) -> None:
        super().__init__("PosterRequest")

    async def save(self, request: PosterRequest) -> None:
        def _save() -> None:
            key = self.get_key(request.id)
            entity = self.client.entity(key=key)
            data = request.model_dump()
            entity.update(data)
            self.client.put(entity)

        await asyncio.to_thread(_save)

    async def get(self, request_id: str) -> PosterRequest | None:
        def _get() -> dict | None:
            key = self.get_key(request_id)
            return self.client.get(key)

        data = await asyncio.to_thread(_get)
        if not data:
            return None
        return PosterRequest(**data)


poster_request_repository = PosterRequestRepository()
