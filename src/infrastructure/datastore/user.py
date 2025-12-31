from google.cloud import datastore
from models.user import User
from infrastructure.datastore.base import DatastoreRepository


class UserDatastoreRepository(DatastoreRepository[User]):
    def __init__(self):
        super().__init__(User.kind)

    def _entity_to_domain(self, entity: datastore.Entity) -> User:
        data = dict(entity)
        # Compatibility with old entities
        if "chat_id" in data:
            data["id"] = data.pop("chat_id")
        if "user_id" in data:
            data["id"] = data.pop("user_id")

        # Ensure all fields exist for the new model
        return User(**data)

    def load(self, entity_id: str | int) -> User | None:
        # 1. Try to load from "User" kind (new or old)
        key = self.get_key(entity_id)
        entity = self.client.get(key)
        if entity:
            return self._entity_to_domain(entity)

        # 2. If not found and it's a positive ID, try to load from "InlineUser" kind
        if isinstance(entity_id, int) and entity_id > 0:
            inline_key = self.client.key("InlineUser", entity_id)
            entity = self.client.get(inline_key)
            if entity:
                user = self._entity_to_domain(entity)
                # We don't save it yet, the service will decide when to save (and thus "migrate" it to "User" kind)
                return user

        return None

    def load_all(self, ignore_gdpr: bool = False) -> list[User]:
        # Load all from "User" kind
        query = self.client.query(kind=self.kind)
        results = [self._entity_to_domain(entity) for entity in query.fetch()]

        # Also load from "InlineUser" and merge if not already in results
        # This is expensive but only for load_all (ranking/metrics)
        inline_query = self.client.query(kind="InlineUser")
        existing_ids = {u.id for u in results}
        for entity in inline_query.fetch():
            user = self._entity_to_domain(entity)
            if user.id not in existing_ids:
                results.append(user)
                existing_ids.add(user.id)

        if ignore_gdpr:
            return results
        return [u for u in results if not u.gdpr]

    def save(self, user: User) -> None:
        key = self.get_key(user.id)
        entity = datastore.Entity(key=key)
        entity.update(user.model_dump())
        self.client.put(entity)


user_repository = UserDatastoreRepository()
# For backward compatibility with imports
inline_user_repository = user_repository
