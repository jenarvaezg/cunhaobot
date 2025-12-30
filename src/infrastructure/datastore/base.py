from typing import Generic, TypeVar
from google.cloud import datastore
from pydantic import BaseModel
from utils.gcp import get_datastore_client

T = TypeVar("T", bound=BaseModel)


class DatastoreRepository(Generic[T]):
    def __init__(self, kind: str):
        self.kind = kind

    @property
    def client(self) -> datastore.Client:
        return get_datastore_client()

    def get_key(self, entity_id: str | int) -> datastore.Key:
        return self.client.key(self.kind, entity_id)

    def delete(self, entity_id: str | int) -> None:
        self.client.delete(self.get_key(entity_id))
