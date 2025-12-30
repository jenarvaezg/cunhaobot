from typing import Optional
from telegram import Update, Message
from models.user import User, InlineUser
from infrastructure.datastore.user import (
    user_repository,
    inline_user_repository,
    UserDatastoreRepository,
    InlineUserDatastoreRepository,
)


class UserService:
    def __init__(
        self,
        user_repo: UserDatastoreRepository = user_repository,
        inline_user_repo: InlineUserDatastoreRepository = inline_user_repository,
    ):
        self.user_repo = user_repo
        self.inline_user_repo = inline_user_repo

    def update_or_create_inline_user(self, update: Update) -> Optional[InlineUser]:
        if not (update_user := update.effective_user):
            return None

        user = self.inline_user_repo.load(update_user.id)

        if user:
            if user.name != update_user.name:
                user.name = update_user.name
                self.inline_user_repo.save(user)
            return user

        user = InlineUser(user_id=update_user.id, name=update_user.name)
        self.inline_user_repo.save(user)
        return user

    def _get_name_from_message(self, msg: Message) -> str:
        if msg.chat.type == msg.chat.PRIVATE:
            return (
                msg.from_user.name
                if msg.from_user and msg.from_user.name
                else "Unknown"
            )
        return msg.chat.title if msg.chat.title else "Unknown"

    def update_or_create_user(self, update: Update) -> Optional[User]:
        message = update.effective_message
        if not message:
            return None

        chat_id = message.chat_id
        name = self._get_name_from_message(message)

        user = self.user_repo.load(chat_id)

        if user:
            user.gdpr = False
            user.name = name
            self.user_repo.save(user)
            return user

        user = User(
            chat_id=chat_id,
            name=name,
            is_group=message.chat.type != message.chat.PRIVATE,
        )
        self.user_repo.save(user)
        return user

    def delete_user(self, user: User, hard: bool = False) -> None:
        if hard:
            self.user_repo.delete(user.chat_id)
        else:
            user.gdpr = True
            self.user_repo.save(user)

    def add_inline_usage(self, user: InlineUser) -> None:
        user.usages += 1
        self.inline_user_repo.save(user)


# Singleton
user_service = UserService()
