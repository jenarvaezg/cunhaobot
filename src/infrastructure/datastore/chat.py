from google.cloud import datastore
from models.chat import Chat
from infrastructure.datastore.base import DatastoreRepository


class ChatDatastoreRepository(DatastoreRepository[Chat]):
    def __init__(self):
        super().__init__(Chat.kind)

    def _entity_to_domain(self, entity: datastore.Entity) -> Chat:
        data = dict(entity)
        if "chat_id" in data:
            data["id"] = data.pop("chat_id")
        return Chat(**data)

    def load(self, entity_id: str | int) -> Chat | None:
        key = self.get_key(entity_id)
        entity = self.client.get(key)
        if entity:
            return self._entity_to_domain(entity)
        return None

    def load_all(self) -> list[Chat]:
        query = self.client.query(kind=self.kind)
        return [self._entity_to_domain(entity) for entity in query.fetch()]

    def save(self, chat: Chat) -> None:
        key = self.get_key(chat.id)
        entity = datastore.Entity(key=key)
        entity.update(chat.model_dump())
        self.client.put(entity)


chat_repository = ChatDatastoreRepository()
