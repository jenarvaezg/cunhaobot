from typing import List

from google.cloud import datastore


class ScheduledTask:
    kind = 'ScheduledTask'

    def __init__(self, chat_id, hour, query, service):
        self.chat_id = chat_id
        self.hour = hour
        self.query = query
        self.service = service

    def __str__(self):
        return f"Chapa a las {self.hour} con parametros '{self.query}'"

    @property
    def datastore_id(self) -> str:
        return f"{self.chat_id}-{self.hour}-{self.query}"

    @classmethod
    def from_entity(cls, entity) -> 'ScheduledTask':
        return cls(
            entity['chat_id'],
            entity['hour'],
            entity['query'],
            entity['service'],
        )

    def save(self) -> None:
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.datastore_id)
        entity = datastore.Entity(key=key)

        entity['chat_id'] = self.chat_id
        entity['hour'] = self.hour
        entity['query'] = self.query
        entity['service'] = self.service

        datastore_client.put(entity)

    def delete(self) -> None:
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.datastore_id)
        datastore_client.delete(key)

    @classmethod
    def get_tasks(cls, **kwargs) -> List['ScheduledTask']:
        datastore_client = datastore.Client()
        query = datastore_client.query(kind=cls.kind)
        for k, v in kwargs.items():
            query.add_filter(k, '=', v)
        return [cls.from_entity(entity) for entity in query.fetch()]

