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

    async def count_completed_by_user(self, user_id: int) -> int:
        def _count() -> int:
            query = self.client.query(kind=self.kind)
            query.add_filter("user_id", "=", user_id)
            query.add_filter("status", "=", "completed")
            return len(list(query.fetch()))

        return await asyncio.to_thread(_count)

    async def get_completed_by_user(self, user_id: int) -> list[PosterRequest]:
        def _fetch() -> list[PosterRequest]:
            query = self.client.query(kind=self.kind)
            query.add_filter("user_id", "=", user_id)
            query.add_filter("status", "=", "completed")
            query.order = ["-message_id"]  # rough sort by time/id
            return [PosterRequest(**e) for e in query.fetch()]

        return await asyncio.to_thread(_fetch)


poster_request_repository = PosterRequestRepository()
