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

    def load(self, entity_id: str | int) -> User | None:
        key = self.get_key(entity_id)
        entity = self.client.get(key)
        if entity:
            return self._entity_to_domain(entity)
        return None

    def load_all(self, ignore_gdpr: bool = False) -> list[User]:
        query = self.client.query(kind=self.kind)
        results = [self._entity_to_domain(entity) for entity in query.fetch()]

        if ignore_gdpr:
            return results
        return [u for u in results if not u.gdpr]

    def save(self, user: User) -> None:
        key = self.get_key(user.id)
        entity = datastore.Entity(key=key)
        entity.update(user.model_dump())
        self.client.put(entity)


user_repository = UserDatastoreRepository()
# For backward compatibility with imports in some legacy files
inline_user_repository = user_repository
