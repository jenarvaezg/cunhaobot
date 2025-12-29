from dataclasses import dataclass
from typing import Optional, Protocol, ClassVar

from google.cloud import datastore
from telegram import Message, Update

from utils.gcp import get_datastore_client


@dataclass(unsafe_hash=True)
class InlineUser:
    user_id: int
    name: str
    usages: int = 0

    kind: ClassVar[str] = "InlineUser"

    @classmethod
    def get_repository(cls) -> "InlineUserRepository":
        return _inline_user_repository

    @classmethod
    def update_or_create_from_update(cls, update: Update) -> Optional["InlineUser"]:
        if not (update_user := update.effective_user):
            return None

        repo = cls.get_repository()

        # Try to load existing
        user = repo.load(update_user.id)

        if user:
            if user.name != update_user.name:
                user.name = update_user.name
                repo.save(user)
            return user

        # Create new
        user = cls(user_id=update_user.id, name=update_user.name)
        repo.save(user)
        return user

    @classmethod
    def get_all(cls) -> list["InlineUser"]:
        return cls.get_repository().get_all()

    def add_usage(self) -> None:
        self.usages += 1
        self.save()

    def save(self) -> None:
        self.get_repository().save(self)


@dataclass(unsafe_hash=True)
class User:
    chat_id: int
    name: str
    is_group: bool
    gdpr: bool = False

    kind: ClassVar[str] = "User"

    @staticmethod
    def _get_name_from_message(msg: Message) -> str:
        if msg.chat.type == msg.chat.PRIVATE:
            return (
                msg.from_user.name
                if msg.from_user and msg.from_user.name
                else "Unknown"
            )
        return msg.chat.title if msg.chat.title else "Unknown"

    @classmethod
    def get_repository(cls) -> "UserRepository":
        return _user_repository

    @classmethod
    def update_or_create_from_update(cls, update: Update) -> Optional["User"]:
        message = update.effective_message
        if not message:
            return None
        chat_id = message.chat_id
        name = cls._get_name_from_message(message)

        repo = cls.get_repository()
        user_from_entity = repo.load(chat_id)

        if user_from_entity:
            user_from_entity.gdpr = False
            user_from_entity.name = name
            repo.save(user_from_entity)
            return user_from_entity

        user = cls(chat_id, name, message.chat.type != message.chat.PRIVATE)
        repo.save(user)
        return user

    def save(self) -> None:
        self.get_repository().save(self)

    @classmethod
    def load(cls, chat_id: int) -> Optional["User"]:
        return cls.get_repository().load(chat_id)

    @classmethod
    def load_all(cls, ignore_gdpr: bool = False) -> list["User"]:
        return cls.get_repository().load_all(ignore_gdpr=ignore_gdpr)

    def delete(self, hard: bool = False) -> None:
        if hard:
            self.get_repository().delete(self.chat_id)
        else:
            self.gdpr = True
            self.save()


# --- Protocols ---


class InlineUserRepository(Protocol):
    def load(self, user_id: int) -> Optional[InlineUser]: ...
    def save(self, user: InlineUser) -> None: ...
    def get_all(self) -> list[InlineUser]: ...


class UserRepository(Protocol):
    def load(self, chat_id: int) -> Optional[User]: ...
    def save(self, user: User) -> None: ...
    def delete(self, chat_id: int) -> None: ...
    def load_all(self, ignore_gdpr: bool = False) -> list[User]: ...


# --- Implementations ---


class DatastoreInlineUserRepository:
    def __init__(self, model_class: type[InlineUser]):
        self.model_class = model_class

    @property
    def client(self) -> datastore.Client:
        return get_datastore_client()

    def _entity_to_domain(self, entity: datastore.Entity) -> InlineUser:
        return self.model_class(
            user_id=entity["user_id"],
            name=entity["name"],
            usages=entity["usages"],
        )

    def load(self, user_id: int) -> Optional[InlineUser]:
        key = self.client.key(self.model_class.kind, user_id)
        entity = self.client.get(key)
        if entity:
            return self._entity_to_domain(entity)
        return None

    def save(self, user: InlineUser) -> None:
        key = self.client.key(self.model_class.kind, user.user_id)
        entity = datastore.Entity(key=key)
        entity.update(
            {"user_id": user.user_id, "name": user.name, "usages": user.usages}
        )
        self.client.put(entity)

    def get_all(self) -> list[InlineUser]:
        query = self.client.query(kind=self.model_class.kind)
        return [self._entity_to_domain(entity) for entity in query.fetch()]


class DatastoreUserRepository:
    def __init__(self, model_class: type[User]):
        self.model_class = model_class

    @property
    def client(self) -> datastore.Client:
        return get_datastore_client()

    def _entity_to_domain(self, entity: datastore.Entity) -> User:
        return self.model_class(
            chat_id=entity["chat_id"],
            name=entity["name"],
            is_group=entity["is_group"],
            gdpr=entity["gdpr"],
        )

    def load(self, chat_id: int) -> Optional[User]:
        key = self.client.key(self.model_class.kind, chat_id)
        entity = self.client.get(key)
        if entity:
            return self._entity_to_domain(entity)
        return None

    def save(self, user: User) -> None:
        key = self.client.key(self.model_class.kind, user.chat_id)
        entity = datastore.Entity(key=key)
        entity.update(
            {
                "chat_id": user.chat_id,
                "name": user.name,
                "is_group": user.is_group,
                "gdpr": user.gdpr,
            }
        )
        self.client.put(entity)

    def delete(self, chat_id: int) -> None:
        key = self.client.key(self.model_class.kind, chat_id)
        self.client.delete(key)

    def load_all(self, ignore_gdpr: bool = False) -> list[User]:
        query = self.client.query(kind=self.model_class.kind)
        if not ignore_gdpr:
            query.add_filter("gdpr", "=", False)
        return [self._entity_to_domain(entity) for entity in query.fetch()]


# --- Instances ---

_inline_user_repository = DatastoreInlineUserRepository(InlineUser)
_user_repository = DatastoreUserRepository(User)
