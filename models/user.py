from typing import List, Tuple, Optional

from google.cloud import datastore


class User:
    kind = 'User'

    def __init__(self, chat_id, name, is_group, gdpr=False):
        self.chat_id = chat_id
        self.name = name
        self.is_group = is_group
        self.gdpr = gdpr

    @staticmethod
    def _get_name_from_message(msg) -> Tuple[str, bool]:
        if msg.chat.type == 'private':
            return msg.from_user.name, False
        else:
            return msg.chat.title, True

    @classmethod
    def from_update(cls, update) -> 'User':
        msg = update.effective_message
        chat_id = msg.chat.id
        name, is_group = cls._get_name_from_message(msg)
        return cls(chat_id, name, is_group)

    @classmethod
    def from_entity(cls, entity) -> 'User':
        return cls(
            entity['chat_id'],
            entity['name'],
            entity['is_group'],
            entity['gdpr'],
        )

    def save(self):
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.chat_id)
        entity = datastore.Entity(key=key)

        entity['chat_id'] = self.chat_id
        entity['name'] = self.name
        entity['is_group'] = self.is_group
        entity['gdpr'] = self.gdpr

        datastore_client.put(entity)

    @classmethod
    def load(cls, chat_id) -> Optional['User']:
        datastore_client = datastore.Client()
        key = datastore_client.key(cls.kind, chat_id)

        entity = datastore_client.get(key)
        if entity is None:
            return entity

        return cls.from_entity(entity)

    @classmethod
    def load_all(cls, ignore_gdpr=False) -> List['User']:
        datastore_client = datastore.Client()
        query = datastore_client.query(kind=cls.kind)
        if not ignore_gdpr:
            query.add_filter('gdpr', '=', False)
        return [cls.from_entity(entity) for entity in query.fetch()]

    def delete(self, hard=False):
        if hard:
            datastore_client = datastore.Client()
            key = datastore_client.key(self.kind, self.chat_id)
            datastore_client.delete(key)
        else:
            self.gdpr = True
            self.save()


