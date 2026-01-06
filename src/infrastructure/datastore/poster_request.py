import asyncio
from google.cloud import datastore
from models.poster_request import PosterRequest
from infrastructure.datastore.base import DatastoreRepository


class PosterRequestRepository(DatastoreRepository[PosterRequest]):
    def __init__(self) -> None:
        super().__init__("PosterRequest")

    def _entity_to_domain(self, entity: datastore.Entity) -> PosterRequest:
        return PosterRequest(**entity)

    async def count_completed_by_user(self, user_id: str | int) -> int:
        def _count() -> int:
            query = self.client.query(kind=self.kind)
            # Handle numeric IDs (Telegram) vs string IDs (others)
            uid = user_id
            if isinstance(user_id, str) and user_id.isdigit():
                uid = int(user_id)

            query.add_filter(filter=datastore.query.PropertyFilter("user_id", "=", uid))
            query.add_filter(
                filter=datastore.query.PropertyFilter("status", "=", "completed")
            )

            count_query = self.client.aggregation_query(query=query)
            count_query.count(alias="all")
            results = list(count_query.fetch())
            if results and len(results) > 0 and len(results[0]) > 0:
                # Also try string fallback if 0 results
                count = int(results[0][0].value)
                if count == 0 and isinstance(uid, int):
                    # Try as string
                    query2 = self.client.query(kind=self.kind)
                    query2.add_filter(
                        datastore.query.PropertyFilter("user_id", "=", str(uid))
                    )
                    query2.add_filter(
                        datastore.query.PropertyFilter("status", "=", "completed")
                    )
                    count_query2 = self.client.aggregation_query(query=query2)
                    count_query2.count(alias="all")
                    results2 = list(count_query2.fetch())
                    if results2:
                        return int(results2[0][0].value)
                return count
            return 0

        return await asyncio.to_thread(_count)

    async def get_completed_by_user(self, user_id: str | int) -> list[PosterRequest]:
        def _fetch() -> list[PosterRequest]:
            # Try numeric first
            uid = user_id
            if isinstance(user_id, str) and user_id.isdigit():
                uid = int(user_id)

            query = self.client.query(kind=self.kind)
            query.add_filter(datastore.query.PropertyFilter("user_id", "=", uid))
            query.add_filter(datastore.query.PropertyFilter("status", "=", "completed"))

            results = [PosterRequest(**e) for e in query.fetch()]

            # Fallback to string if empty
            if not results and isinstance(uid, int):
                query2 = self.client.query(kind=self.kind)
                query2.add_filter(
                    datastore.query.PropertyFilter("user_id", "=", str(uid))
                )
                query2.add_filter(
                    datastore.query.PropertyFilter("status", "=", "completed")
                )
                results = [PosterRequest(**e) for e in query2.fetch()]

            results.sort(key=lambda x: x.message_id or 0, reverse=True)
            return results

        return await asyncio.to_thread(_fetch)


poster_request_repository = PosterRequestRepository()
