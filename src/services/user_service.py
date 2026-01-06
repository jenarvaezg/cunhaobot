import logging
import secrets
from datetime import datetime, timezone
from typing import TYPE_CHECKING, cast
from telegram import Update
from models.user import User
from models.chat import Chat
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from models.link_request import LinkRequest

if TYPE_CHECKING:
    from infrastructure.protocols import (
        UserRepository,
        ChatRepository,
        PhraseRepository,
        LongPhraseRepository,
        ProposalRepository,
        LongProposalRepository,
        LinkRequestRepository,
    )

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        chat_repo: ChatRepository,
        phrase_repo: PhraseRepository,
        long_phrase_repo: LongPhraseRepository,
        proposal_repo: ProposalRepository,
        long_proposal_repo: LongProposalRepository,
        link_request_repo: LinkRequestRepository,
    ):
        self.user_repo = user_repo
        self.chat_repo = chat_repo
        self.phrase_repo = phrase_repo
        self.long_phrase_repo = long_phrase_repo
        self.proposal_repo = proposal_repo
        self.long_proposal_repo = long_proposal_repo
        self.link_request_repo = link_request_repo

    async def get_user(
        self, user_id: str | int, platform: str | None = None
    ) -> User | None:
        user = await self.user_repo.load(user_id)

        # Fallback: try converting string to int if it's a digit string (handling numeric IDs)
        if not user and isinstance(user_id, str) and user_id.lstrip("-").isdigit():
            try:
                user = await self.user_repo.load(int(user_id))
            except ValueError:
                pass

        if not user:
            return None

        # If we followed a link (IDs don't match), we allow different platforms.
        # If it's a direct load, we still enforce the platform check for safety.
        if platform and str(user.id) == str(user_id) and user.platform != platform:
            return None

        return user

    async def get_chat(
        self, chat_id: str | int, platform: str | None = None
    ) -> Chat | None:
        chat = await self.chat_repo.load(chat_id)
        if chat and platform and chat.platform != platform:
            return None
        return chat

    async def save_user(self, user: User) -> None:
        await self.user_repo.save(user)

    async def save_chat(self, chat: Chat) -> None:
        await self.chat_repo.save(chat)

    async def update_user_data(
        self,
        user_id: str | int,
        name: str,
        username: str | None = None,
        platform: str = "telegram",
    ) -> User:
        user = await self.user_repo.load(user_id)

        if user:
            changed = False
            is_master = str(user.id) == str(user_id)

            if user.name != name:
                user.name = name
                changed = True
            if user.username != username:
                user.username = username
                changed = True
            if user.gdpr:
                user.gdpr = False
                changed = True

            # Only update platform if this is the master record being loaded directly
            if is_master and user.platform != platform:
                user.platform = platform
                changed = True

            if changed:
                await self.user_repo.save(user)
            return user

        user = User(
            id=user_id,
            name=name,
            username=username,
            platform=platform,
        )
        await self.user_repo.save(user)
        return user

    async def update_chat_data(
        self,
        chat_id: str | int,
        title: str,
        chat_type: str,
        username: str | None = None,
        platform: str = "telegram",
    ) -> Chat:
        chat = await self.chat_repo.load(chat_id)
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

            await self.chat_repo.save(chat)
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
        await self.chat_repo.save(chat)
        return chat

    async def update_or_create_inline_user(self, update: Update) -> User | None:
        if not (update_user := update.effective_user):
            return None

        return await self.update_user_data(
            user_id=update_user.id,
            name=update_user.name,
            username=update_user.username,
            platform="telegram",
        )

    async def update_or_create_user(self, update: Update) -> User | None:
        """Updates or creates both User (the person) and Chat (the context)."""
        message = update.effective_message
        user = update.effective_user
        if not message or not user:
            return None

        # 1. Update/Create User (the person)
        user_id = user.id
        user_name = user.name
        user_username = user.username

        db_user = await self.update_user_data(
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

        await self.update_chat_data(
            chat_id=chat_id,
            title=chat_title or "Unknown",
            chat_type=chat_type,
            username=chat_username,
            platform="telegram",
        )

        return db_user

    async def update_or_create_slack_user(
        self,
        slack_user_id: str,
        name: str,
        username: str | None = None,
    ) -> User:
        return await self.update_user_data(
            user_id=slack_user_id,
            name=name,
            username=username,
            platform="slack",
        )

    async def delete_user(self, user: User, hard: bool = False) -> None:
        if hard:
            await self.user_repo.delete(user.id)
        else:
            user.gdpr = True
            await self.user_repo.save(user)

    async def add_inline_usage(self, user: User) -> None:
        user.usages += 1
        user.points += 1
        await self.user_repo.save(user)

    async def toggle_privacy(self, user_id: str | int, platform: str) -> bool | None:
        user = await self.get_user(user_id, platform)
        if not user:
            return None

        user.is_private = not user.is_private
        await self.save_user(user)
        return user.is_private

    async def add_points(self, user_id: str | int, points: int) -> None:
        if user_id == 0:
            return

        user = await self.user_repo.load(user_id)
        if user:
            user.points += points
            await self.user_repo.save(user)
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

        from tg import get_initialized_tg_application

        try:
            application = await get_initialized_tg_application()

            bot = application.bot
            photos = await bot.get_user_profile_photos(target_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][0].file_id
                file = await bot.get_file(file_id)
                return await file.download_as_bytearray()
        except Exception as e:
            logger.error(f"Error getting user photo for {target_id}: {e}")
        return None

    async def generate_link_token(self, user_id: str | int, platform: str) -> str:
        token = secrets.token_hex(3).upper()
        request = LinkRequest(
            token=token, source_user_id=user_id, source_platform=platform
        )
        await self.link_request_repo.save(request)
        return token

    async def complete_link(
        self, token: str, target_user_id: str | int, target_platform: str
    ) -> bool:
        request = await self.link_request_repo.load(token)
        if not request:
            return False

        if request.expires_at.tzinfo is None:
            expires_at = request.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = request.expires_at

        if expires_at < datetime.now(timezone.utc):
            await self.link_request_repo.delete(token)
            return False

        source_user_id = request.source_user_id
        source_platform = request.source_platform

        if (
            str(source_user_id) == str(target_user_id)
            and source_platform == target_platform
        ):
            return False

        source_user = await self.user_repo.load_raw(source_user_id)
        target_user = await self.user_repo.load(
            target_user_id
        )  # Target should be the ultimate master

        if not source_user or not target_user:
            return False

        if str(source_user.id) == str(target_user.id):
            return False

        # Merge Stats
        target_user.points += source_user.points
        target_user.usages += source_user.usages
        target_user.badges = list(set(target_user.badges + source_user.badges))
        if "multiplataforma" not in target_user.badges:
            target_user.badges.append("multiplataforma")

        await self.save_user(target_user)

        # Migrate Content Ownership
        phrases = await self.phrase_repo.get_phrases(user_id=str(source_user.id))
        for p in phrases:
            p.user_id = target_user.id
            await self.phrase_repo.save(cast(Phrase, p))

        long_phrases = await self.long_phrase_repo.get_phrases(
            user_id=str(source_user.id)
        )
        for lp in long_phrases:
            lp.user_id = target_user.id
            await self.long_phrase_repo.save(cast(LongPhrase, lp))

        proposals = await self.proposal_repo.get_proposals(
            user_id=str(source_user.id), limit=1000
        )
        for prop in proposals:
            prop.user_id = target_user.id
            await self.proposal_repo.save(cast(Proposal, prop))

        long_proposals = await self.long_proposal_repo.get_proposals(
            user_id=str(source_user.id), limit=1000
        )
        for lprop in long_proposals:
            lprop.user_id = target_user.id
            await self.long_proposal_repo.save(cast(LongProposal, lprop))

        # Instead of deleting, we make source_user an alias of target_user
        source_user.linked_to = target_user.id
        source_user.points = 0
        source_user.usages = 0
        source_user.badges = []
        await self.save_user(source_user)

        await self.link_request_repo.delete(token)

        return True
