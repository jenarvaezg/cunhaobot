from typing import List, Optional

from google.cloud import datastore
from telegram import Update, Message


class InlineUser:
    kind = 'InlineUser'

    def __init__(self, user_id: int, name: str, usages: int = 0):
        self.user_id = user_id
        self.name = name
        self.usages = usages

    @property
    def datastore_key(self) -> datastore.Key:
        return datastore.Client().key(self.kind, self.user_id)

    @classmethod
    def update_or_create_from_update(cls, update: Update) -> 'InlineUser':
        datastore_client = datastore.Client()
        update_user = update.effective_user
        user = cls(update_user.id, update_user.name)

        entity = datastore_client.get(user.datastore_key)
        if entity:
            user_from_entity = cls.from_entity(entity)
            if user_from_entity.name != update_user.name:
                user_from_entity.name = update_user.name
                user.save()
            return user_from_entity

        user.save()
        return user

    @classmethod
    def from_entity(cls, entity: datastore.Entity) -> 'InlineUser':
        return cls(
            entity['user_id'],
            entity['name'],
            entity['usages'],
        )

    @classmethod
    def get_all(cls) -> List['InlineUser']:
        datastore_client = datastore.Client()
        query = datastore_client.query(kind=cls.kind)
        return [cls.from_entity(entity) for entity in query.fetch()]

    def add_usage(self) -> None:
        self.usages += 1
        self.save()

    def save(self) -> None:
        datastore_client = datastore.Client()
        entity = datastore.Entity(key=self.datastore_key)

        entity['user_id'] = self.user_id
        entity['name'] = self.name
        entity['usages'] = self.usages

        datastore_client.put(entity)


class User:
    kind = 'User'

    def __init__(self, chat_id, name, is_group, gdpr=False):
        self.chat_id = chat_id
        self.name = name
        self.is_group = is_group
        self.gdpr = gdpr

    @staticmethod
    def _get_name_from_message(msg: Message) -> str:
        return msg.from_user.name if msg.chat.type == msg.chat.PRIVATE else msg.chat.title

    @classmethod
    def update_or_create_from_update(cls, update) -> 'User':
        message: Message = update.effective_message
        if not message:
            return None
        chat_id = message.chat_id
        name = cls._get_name_from_message(message)
        user = cls(chat_id, name, message.chat.type != message.chat.PRIVATE)

        user_from_entity = cls.load(chat_id)
        if user_from_entity:
            user_from_entity.gdpr = False
            user_from_entity.name = name
            user.save()

        return user

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

        return cls.from_entity(entity) if entity else None

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


