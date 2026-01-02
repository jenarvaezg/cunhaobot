import logging
import secrets
from datetime import datetime
from telegram import Update, Message
from models.user import User
from models.link_request import LinkRequest
from infrastructure.datastore.user import (
    user_repository,
    UserDatastoreRepository,
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
    ):
        self.user_repo = user_repo

    def get_user(self, user_id: str | int, platform: str | None = None) -> User | None:
        user = self.user_repo.load(user_id)

        # Fallback: try converting string to int if it's a digit string (handling negative IDs)
        if not user and isinstance(user_id, str) and user_id.lstrip("-").isdigit():
            try:
                user = self.user_repo.load(int(user_id))
            except ValueError:
                pass

        if user and platform and user.platform != platform:
            return None
        return user

    def save_user(self, user: User) -> None:
        self.user_repo.save(user)

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

    def update_or_create_inline_user(self, update: Update) -> User | None:
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

    def update_or_create_user(self, update: Update) -> User | None:
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

        # Convert to int if possible (for Telegram IDs passed as strings from web routes)
        target_id: int | None = None
        if isinstance(user_id, int):
            target_id = user_id
        elif isinstance(user_id, str) and user_id.lstrip("-").isdigit():
            target_id = int(user_id)

        if target_id is None:
            # Probably Slack or other platform with non-numeric IDs, we don't support it yet
            return None

        from tg import get_tg_application

        try:
            application = get_tg_application()
            if not application.running:
                await application.initialize()

            bot = application.bot
            photos = await bot.get_user_profile_photos(target_id, limit=1)
            if photos.total_count > 0:
                # Get the smallest photo to be fast
                file_id = photos.photos[0][0].file_id
                file = await bot.get_file(file_id)
                return await file.download_as_bytearray()
        except Exception as e:
            logger.error(f"Error getting user photo for {target_id}: {e}")
        return None

    def generate_link_token(self, user_id: str | int, platform: str) -> str:
        token = secrets.token_hex(3).upper()  # 6 chars
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

        if request.expires_at < datetime.now():
            link_request_repository.delete(token)
            return False

        # Source user is the one who generated the token (to be merged FROM)
        # Target user is the one claiming the token (to be merged TO)
        # WAIT: Usually "Link my account" means "I am X, add Y to me".
        # If I am on Telegram (X) and say /link, I get a token.
        # I go to Slack (Y) and say /link <token>.
        # Which one keeps identity?
        # Usually the one where I enter the code becomes the "Primary" or "Linked".
        # Let's say I want to KEEP Telegram identity.
        # I generate token on Slack. I enter token on Telegram.
        # Telegram (Target) absorbs Slack (Source).
        # So Source (Token Generator) -> Merges INTO -> Target (Token Consumer).

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

        # Merge Data
        target_user.points += source_user.points
        target_user.usages += source_user.usages
        # Merge badges unique
        target_user.badges = list(set(target_user.badges + source_user.badges))

        # Save Target
        self.save_user(target_user)

        # Migrate Content Ownership
        # Phrases
        phrases = phrase_repository.get_phrases(user_id=str(source_user.id))
        for p in phrases:
            p.user_id = target_user.id
            phrase_repository.save(p)

        long_phrases = long_phrase_repository.get_phrases(user_id=str(source_user.id))
        for lp in long_phrases:
            lp.user_id = target_user.id
            long_phrase_repository.save(lp)

        # Proposals
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

        # Delete Source
        self.delete_user(source_user, hard=True)
        link_request_repository.delete(token)

        return True


# Singleton
user_service = UserService()
