from google.cloud import datastore
from models.chat import Chat
from infrastructure.datastore.base import DatastoreRepository


class ChatDatastoreRepository(DatastoreRepository[Chat]):
    def __init__(self):
        super().__init__("Chat")

    def _entity_to_domain(self, entity: datastore.Entity) -> Chat:
        data = dict(entity)
        if "chat_id" in data:
            data["id"] = data.pop("chat_id")
        return Chat(**data)


chat_repository = ChatDatastoreRepository()
