from google.cloud import datastore
from models.user import User, InlineUser
from infrastructure.datastore.base import DatastoreRepository


class UserDatastoreRepository(DatastoreRepository[User]):
    def __init__(self):
        super().__init__(User.kind)

    def _entity_to_domain(self, entity: datastore.Entity) -> User:
        return User(**dict(entity))

    def load(self, entity_id: str | int) -> User | None:
        key = self.get_key(entity_id)
        entity = self.client.get(key)
        return self._entity_to_domain(entity) if entity else None

    def load_all(self, ignore_gdpr: bool = False) -> list[User]:
        query = self.client.query(kind=self.kind)
        results = [self._entity_to_domain(entity) for entity in query.fetch()]
        return results if ignore_gdpr else [u for u in results if not u.gdpr]

    def save(self, user: User) -> None:
        key = self.get_key(user.chat_id)
        entity = datastore.Entity(key=key)
        entity.update(user.model_dump())
        self.client.put(entity)


class InlineUserDatastoreRepository(DatastoreRepository[InlineUser]):
    def __init__(self):
        super().__init__(InlineUser.kind)

    def _entity_to_domain(self, entity: datastore.Entity) -> InlineUser:
        return InlineUser(**dict(entity))

    def load(self, entity_id: str | int) -> InlineUser | None:
        key = self.get_key(entity_id)
        entity = self.client.get(key)
        return self._entity_to_domain(entity) if entity else None

    def load_all(self) -> list[InlineUser]:
        query = self.client.query(kind=self.kind)
        return [self._entity_to_domain(entity) for entity in query.fetch()]

    def save(self, user: InlineUser) -> None:
        key = self.get_key(user.user_id)
        entity = datastore.Entity(key=key)
        entity.update(user.model_dump())
        self.client.put(entity)


user_repository = UserDatastoreRepository()
inline_user_repository = InlineUserDatastoreRepository()
