import asyncio
from google.cloud import datastore
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

    async def count_completed_by_user(self, user_id: str | int) -> int:
        def _count() -> int:
            query = self.client.query(kind=self.kind)
            query.add_filter(
                filter=datastore.query.PropertyFilter("user_id", "=", str(user_id))
            )
            query.add_filter(
                filter=datastore.query.PropertyFilter("status", "=", "completed")
            )

            count_query = self.client.aggregation_query(query=query)
            count_query.count(alias="all")
            results = list(count_query.fetch())
            if results and len(results) > 0 and len(results[0]) > 0:
                return int(results[0][0].value)
            return 0

        return await asyncio.to_thread(_count)

    async def get_completed_by_user(self, user_id: str | int) -> list[PosterRequest]:
        def _fetch() -> list[PosterRequest]:
            query = self.client.query(kind=self.kind)
            query.add_filter(
                filter=datastore.query.PropertyFilter("user_id", "=", str(user_id))
            )
            query.add_filter(
                filter=datastore.query.PropertyFilter("status", "=", "completed")
            )
            # Removed order by message_id to avoid composite index requirement
            results = [PosterRequest(**e) for e in query.fetch()]
            # Sort in memory instead
            results.sort(key=lambda x: x.message_id or 0, reverse=True)
            return results

        return await asyncio.to_thread(_fetch)


poster_request_repository = PosterRequestRepository()
