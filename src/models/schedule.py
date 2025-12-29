from dataclasses import dataclass
from typing import ClassVar, Protocol

from google.cloud import datastore

from utils.gcp import get_datastore_client


@dataclass(unsafe_hash=True)
class ScheduledTask:
    chat_id: int
    hour: int
    minute: int
    query: str
    service: str
    type: str

    kind: ClassVar[str] = "ScheduledTask"

    def __init__(
        self,
        chat_id: int,
        hour: int,
        minute: int,
        query: str,
        service: str,
        type: str = "",
        task_type: str = "",
    ):
        self.chat_id = chat_id
        self.hour = hour
        self.minute = minute
        self.query = query
        self.service = service
        self.type = type or task_type

    def __str__(self) -> str:
        return f"{self.type.capitalize()} a las {self.hour}:{self.minute:02} con parametros '{self.query}'"

    @property
    def datastore_id(self) -> str:
        return f"{self.type}-{self.chat_id}-{self.hour}:{self.minute}-{self.query}"

    @classmethod
    def get_repository(cls) -> "ScheduledTaskRepository":
        return _scheduled_task_repository

    def save(self) -> None:
        self.get_repository().save(self)

    def delete(self) -> None:
        self.get_repository().delete(self.datastore_id)

    @classmethod
    def get_tasks(cls, **kwargs) -> list["ScheduledTask"]:
        return cls.get_repository().get_tasks(**kwargs)


# --- Repository Protocol ---


class ScheduledTaskRepository(Protocol):
    def save(self, task: ScheduledTask) -> None: ...
    def delete(self, task_id: str) -> None: ...
    def get_tasks(self, **kwargs) -> list[ScheduledTask]: ...


# --- Datastore Implementation ---


class DatastoreScheduledTaskRepository:
    def __init__(self, model_class: type[ScheduledTask]):
        self.model_class = model_class

    @property
    def client(self) -> datastore.Client:
        return get_datastore_client()

    def _entity_to_domain(self, entity: datastore.Entity) -> ScheduledTask:
        return self.model_class(
            chat_id=entity["chat_id"],
            hour=entity["hour"],
            minute=entity["minute"],
            query=entity["query"],
            service=entity["service"],
            type=entity["type"],
        )

    def save(self, task: ScheduledTask) -> None:
        key = self.client.key(self.model_class.kind, task.datastore_id)
        entity = datastore.Entity(key=key)
        entity.update(
            {
                "chat_id": task.chat_id,
                "hour": task.hour,
                "minute": task.minute,
                "query": task.query,
                "service": task.service,
                "type": task.type,
            }
        )
        self.client.put(entity)

    def delete(self, task_id: str) -> None:
        key = self.client.key(self.model_class.kind, task_id)
        self.client.delete(key)

    def get_tasks(self, **kwargs) -> list[ScheduledTask]:
        query = self.client.query(kind=self.model_class.kind)
        for k, v in kwargs.items():
            query.add_filter(k, "=", v)
        return [self._entity_to_domain(entity) for entity in query.fetch()]


# --- Instance ---

_scheduled_task_repository = DatastoreScheduledTaskRepository(ScheduledTask)
