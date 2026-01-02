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

    def load(self, entity_id: str | int, follow_link: bool = True) -> User | None:
        key = self.get_key(entity_id)
        entity = self.client.get(key)
        if not entity:
            return None
        user = self._entity_to_domain(entity)
        if follow_link and user.linked_to:
            # Recursively load the master user, but avoid infinite loops
            # by limiting recursion or keeping track of visited IDs (simpler here: just one jump is expected, but let's be safe)
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

    def load_raw(self, entity_id: str | int) -> User | None:
        """Loads the user entity without following linked_to."""
        return self.load(entity_id, follow_link=False)

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
