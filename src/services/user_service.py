import logging
import secrets
from datetime import datetime, timezone
from telegram import Update
from models.user import User
from models.chat import Chat
from models.link_request import LinkRequest
from infrastructure.datastore.user import (
    user_repository,
    UserDatastoreRepository,
)
from infrastructure.datastore.chat import (
    chat_repository,
    ChatDatastoreRepository,
)
from infrastructure.datastore.link_request import link_request_repository
from infrastructure.datastore.phrase import phrase_repository, long_phrase_repository
from infrastructure.datastore.proposal import (
    proposal_repository,
    long_proposal_repository,
)

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserDatastoreRepository = user_repository,
        chat_repo: ChatDatastoreRepository = chat_repository,
    ):
        self.user_repo = user_repo
        self.chat_repo = chat_repo

    def get_user(self, user_id: str | int, platform: str | None = None) -> User | None:
        user = self.user_repo.load(user_id)

        # Fallback: try converting string to int if it's a digit string (handling numeric IDs)
        if not user and isinstance(user_id, str) and user_id.lstrip("-").isdigit():
            try:
                user = self.user_repo.load(int(user_id))
            except ValueError:
                pass

        if user and platform and user.platform != platform:
            return None
        return user

    def get_chat(self, chat_id: str | int, platform: str | None = None) -> Chat | None:
        chat = self.chat_repo.load(chat_id)
        if chat and platform and chat.platform != platform:
            return None
        return chat

    def save_user(self, user: User) -> None:
        self.user_repo.save(user)

    def save_chat(self, chat: Chat) -> None:
        self.chat_repo.save(chat)

    def _update_or_create_user(
        self,
        user_id: str | int,
        name: str,
        username: str | None = None,
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

            if changed:
                self.user_repo.save(user)
            return user

        user = User(
            id=user_id,
            name=name,
            username=username,
            platform=platform,
        )
        self.user_repo.save(user)
        return user

    def _update_or_create_chat(
        self,
        chat_id: str | int,
        title: str,
        chat_type: str,
        username: str | None = None,
        platform: str = "telegram",
    ) -> Chat:
        chat = self.chat_repo.load(chat_id)
        now = datetime.now(timezone.utc)

        if chat:
            if chat.title != title:
                chat.title = title
            if chat.username != username:
                chat.username = username
            if chat.type != chat_type:
                chat.type = chat_type
            if chat.platform != platform:
                chat.platform = platform

            # Always update last_seen and ensure it's active
            chat.last_seen_at = now
            chat.is_active = True
            chat.usages += 1

            self.chat_repo.save(chat)
            return chat

        chat = Chat(
            id=chat_id,
            title=title,
            username=username,
            type=chat_type,
            platform=platform,
            usages=1,
            is_active=True,
            last_seen_at=now,
        )
        self.chat_repo.save(chat)
        return chat

    def update_or_create_inline_user(self, update: Update) -> User | None:
        if not (update_user := update.effective_user):
            return None

        return self._update_or_create_user(
            user_id=update_user.id,
            name=update_user.name,
            username=update_user.username,
            platform="telegram",
        )

    def update_or_create_user(self, update: Update) -> User | None:
        """Updates or creates both User (the person) and Chat (the context)."""
        message = update.effective_message
        user = update.effective_user
        if not message or not user:
            return None

        # 1. Update/Create User (the person)
        user_id = user.id
        user_name = user.name
        user_username = user.username

        db_user = self._update_or_create_user(
            user_id=user_id,
            name=user_name,
            username=user_username,
            platform="telegram",
        )

        # 2. Update/Create Chat (the context)
        chat_id = message.chat_id
        chat_title = (
            message.chat.title
            if message.chat.type != message.chat.PRIVATE
            else user_name
        )
        chat_type = message.chat.type
        chat_username = message.chat.username

        self._update_or_create_chat(
            chat_id=chat_id,
            title=chat_title or "Unknown",
            chat_type=chat_type,
            username=chat_username,
            platform="telegram",
        )

        return db_user

    def update_or_create_slack_user(
        self,
        slack_user_id: str,
        name: str,
        username: str | None = None,
        is_group: bool = False,
    ) -> User:
        # For Slack, we might still want to know if it's a group to create a Chat
        # but the request was specifically about User model.
        # For now, we just update the user.
        return self._update_or_create_user(
            user_id=slack_user_id,
            name=name,
            username=username,
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

    def toggle_privacy(self, user_id: str | int, platform: str) -> bool | None:
        user = self.get_user(user_id, platform)
        if not user:
            return None

        user.is_private = not user.is_private
        self.save_user(user)
        return user.is_private

    def add_points(self, user_id: str | int, points: int) -> None:
        if user_id == 0:
            return

        user = self.user_repo.load(user_id)
        if user:
            user.points += points
            self.user_repo.save(user)
        else:
            # If user not found, we don't award points until they interact
            pass

    async def get_user_photo(self, user_id: str | int) -> bytes | None:
        if not user_id:
            return None

        target_id: int | None = None
        if isinstance(user_id, int):
            target_id = user_id
        elif isinstance(user_id, str) and user_id.lstrip("-").isdigit():
            target_id = int(user_id)

        if target_id is None:
            return None

        from tg import get_tg_application

        try:
            application = get_tg_application()
            if not application.running:
                await application.initialize()

            bot = application.bot
            photos = await bot.get_user_profile_photos(target_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][0].file_id
                file = await bot.get_file(file_id)
                return await file.download_as_bytearray()
        except Exception as e:
            logger.error(f"Error getting user photo for {target_id}: {e}")
        return None

    def generate_link_token(self, user_id: str | int, platform: str) -> str:
        token = secrets.token_hex(3).upper()
        request = LinkRequest(
            token=token, source_user_id=user_id, source_platform=platform
        )
        link_request_repository.save(request)
        return token

    def complete_link(
        self, token: str, target_user_id: str | int, target_platform: str
    ) -> bool:
        request = link_request_repository.load(token)
        if not request:
            return False

        if request.expires_at.tzinfo is None:
            expires_at = request.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = request.expires_at

        if expires_at < datetime.now(timezone.utc):
            link_request_repository.delete(token)
            return False

        source_user_id = request.source_user_id
        source_platform = request.source_platform

        if (
            str(source_user_id) == str(target_user_id)
            and source_platform == target_platform
        ):
            return False

        source_user = self.get_user(source_user_id, source_platform)
        target_user = self.get_user(target_user_id, target_platform)

        if not source_user or not target_user:
            return False

        target_user.points += source_user.points
        target_user.usages += source_user.usages
        target_user.badges = list(set(target_user.badges + source_user.badges))

        self.save_user(target_user)

        # Migrate Content Ownership
        phrases = phrase_repository.get_phrases(user_id=str(source_user.id))
        for p in phrases:
            p.user_id = target_user.id
            phrase_repository.save(p)

        long_phrases = long_phrase_repository.get_phrases(user_id=str(source_user.id))
        for lp in long_phrases:
            lp.user_id = target_user.id
            long_phrase_repository.save(lp)

        proposals = proposal_repository.get_proposals(
            user_id=str(source_user.id), limit=1000
        )
        for prop in proposals:
            prop.user_id = target_user.id
            proposal_repository.save(prop)

        long_proposals = long_proposal_repository.get_proposals(
            user_id=str(source_user.id), limit=1000
        )
        for lprop in long_proposals:
            lprop.user_id = target_user.id
            long_proposal_repository.save(lprop)

        self.delete_user(source_user, hard=True)
        link_request_repository.delete(token)

        return True


# Singleton
user_service = UserService()
