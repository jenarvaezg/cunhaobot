import logging
from typing import Optional
from telegram import Update, Message
from models.user import User
from infrastructure.datastore.user import (
    user_repository,
    UserDatastoreRepository,
)

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserDatastoreRepository = user_repository,
    ):
        self.user_repo = user_repo

    def _update_or_create(
        self,
        user_id: str | int,
        name: str,
        username: str | None = None,
        is_group: bool = False,
        platform: str = "telegram",
    ) -> User:
        user = self.user_repo.load(user_id)

        if user:
            changed = False
            if user.name != name:
                user.name = name
                changed = True
            if user.username != username:
                user.username = username
                changed = True
            if user.gdpr:
                user.gdpr = False
                changed = True
            if user.platform != platform:
                user.platform = platform
                changed = True
            # In case it was loaded from InlineUser kind, it might not have is_group set correctly
            if not is_group and user.is_group:
                user.is_group = False
                changed = True

            if changed:
                self.user_repo.save(user)
            return user

        user = User(
            id=user_id,
            name=name,
            username=username,
            is_group=is_group,
            platform=platform,
        )
        self.user_repo.save(user)
        return user

    def update_or_create_inline_user(self, update: Update) -> Optional[User]:
        if not (update_user := update.effective_user):
            return None

        return self._update_or_create(
            user_id=update_user.id,
            name=update_user.name,
            username=update_user.username,
            is_group=False,
            platform="telegram",
        )

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
        username = message.from_user.username if message.from_user else None
        is_group = message.chat.type != message.chat.PRIVATE

        return self._update_or_create(
            user_id=chat_id,
            name=name,
            username=username,
            is_group=is_group,
            platform="telegram",
        )

    def update_or_create_slack_user(
        self,
        slack_user_id: str,
        name: str,
        username: str | None = None,
        is_group: bool = False,
    ) -> User:
        return self._update_or_create(
            user_id=slack_user_id,
            name=name,
            username=username,
            is_group=is_group,
            platform="slack",
        )

    def delete_user(self, user: User, hard: bool = False) -> None:
        if hard:
            self.user_repo.delete(user.id)
        else:
            user.gdpr = True
            self.user_repo.save(user)

    def add_inline_usage(self, user: User) -> None:
        user.usages += 1
        user.points += 1
        self.user_repo.save(user)

    def add_points(self, user_id: str | int, points: int) -> None:
        if user_id == 0:
            return

        user = self.user_repo.load(user_id)
        if user:
            # We only award points to individuals, but we can store them in group entities too?
            # Usually points are for the person. In Telegram, a group chat_id is negative.
            # If the ID is from a person, it will be positive.
            user.points += points
            self.user_repo.save(user)
        else:
            # If user not found, we could create a stub but we don't have the name.
            # For now, if they are not in our DB, they don't get points until they interact.
            pass

    async def get_user_photo(self, user_id: str | int) -> bytes | None:
        if not user_id:
            return None

        # For now, only telegram supports photo fetching
        if isinstance(user_id, str):
            # Probably Slack or other platform, we don't support it yet
            return None

        if user_id <= 0:
            return None

        from tg import get_tg_application

        try:
            application = get_tg_application()
            if not application.running:
                await application.initialize()

            bot = application.bot
            photos = await bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                # Get the smallest photo to be fast
                file_id = photos.photos[0][0].file_id
                file = await bot.get_file(file_id)
                return await file.download_as_bytearray()
        except Exception as e:
            logger.error(f"Error getting user photo for {user_id}: {e}")
        return None


# Singleton
user_service = UserService()
