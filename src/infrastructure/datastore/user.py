import asyncio
from google.cloud import datastore
from models.user import User
from infrastructure.datastore.base import DatastoreRepository


class UserDatastoreRepository(DatastoreRepository[User]):
    def __init__(self):
        super().__init__(User.kind)

    def _entity_to_domain(self, entity: datastore.Entity) -> User:
        data = dict(entity)
        # We assume data is now normalized after migration
        return User(**data)

    async def load(self, entity_id: str | int, follow_link: bool = True) -> User | None:
        if not follow_link:
            return await super().load(entity_id)

        def _get():
            key = self.get_key(entity_id)
            entity = self.client.get(key)
            if not entity:
                return None
            user = self._entity_to_domain(entity)
            if user.linked_to:
                visited = {entity_id}
                current_user = user
                while current_user.linked_to and current_user.linked_to not in visited:
                    visited.add(current_user.linked_to)
                    master_key = self.get_key(current_user.linked_to)
                    master_entity = self.client.get(master_key)
                    if not master_entity:
                        break
                    current_user = self._entity_to_domain(master_entity)
                return current_user
            return user

        return await asyncio.to_thread(_get)

    async def load_raw(self, entity_id: str | int) -> User | None:
        """Loads the user entity without following linked_to."""
        return await self.load(entity_id, follow_link=False)

    async def load_all(self, ignore_gdpr: bool = False) -> list[User]:
        results = await super().load_all()
        if ignore_gdpr:
            return results
        return [u for u in results if not u.gdpr]

    async def get_by_username(self, username: str) -> User | None:
        def _query():
            query = self.client.query(kind=self.kind)
            # Normalize username just in case, though DB should store without @
            clean_username = username.lstrip("@")
            query.add_filter("username", "=", clean_username)
            results = list(query.fetch(limit=1))
            if not results:
                return None
            return self._entity_to_domain(results[0])

        return await asyncio.to_thread(_query)


user_repository = UserDatastoreRepository()
# For backward compatibility with imports in some legacy files
inline_user_repository = user_repository
