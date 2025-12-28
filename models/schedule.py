from google.cloud import datastore


class ScheduledTask:
    kind = "ScheduledTask"

    def __init__(self, chat_id, hour, minute, query, service, task_type):
        self.chat_id = chat_id
        self.hour = hour
        self.minute = minute
        self.query = query
        self.service = service
        self.type = task_type

    def __str__(self):
        return f"{self.type.capitalize()} a las {self.hour}:{self.minute:02} con parametros '{self.query}'"

    @property
    def datastore_id(self) -> str:
        return f"{self.type}-{self.chat_id}-{self.hour}:{self.minute}-{self.query}"

    @classmethod
    def from_entity(cls, entity) -> "ScheduledTask":
        return cls(
            entity["chat_id"],
            entity["hour"],
            entity["minute"],
            entity["query"],
            entity["service"],
            entity["type"],
        )

    def save(self) -> None:
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.datastore_id)
        entity = datastore.Entity(key=key)

        entity["chat_id"] = self.chat_id
        entity["hour"] = self.hour
        entity["minute"] = self.minute
        entity["query"] = self.query
        entity["service"] = self.service
        entity["type"] = self.type

        datastore_client.put(entity)

    def delete(self) -> None:
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.datastore_id)
        datastore_client.delete(key)

    @classmethod
    def get_tasks(cls, **kwargs) -> list["ScheduledTask"]:
        datastore_client = datastore.Client()
        query = datastore_client.query(kind=cls.kind)
        for k, v in kwargs.items():
            query.add_filter(k, "=", v)
        return [cls.from_entity(entity) for entity in query.fetch()]
