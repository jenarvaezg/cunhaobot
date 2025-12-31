import logging
import time
import uuid

from google.cloud import datastore
from slack_sdk.oauth.installation_store import Bot, Installation
from slack_sdk.oauth.installation_store.async_installation_store import (
    AsyncInstallationStore,
)
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore

from infrastructure.datastore.base import DatastoreRepository
from models.slack import SlackBot, SlackInstallation

logger = logging.getLogger(__name__)


class DatastoreOAuthStateStore(AsyncOAuthStateStore):
    def __init__(self, expiration_seconds: int = 600):
        self.repo = DatastoreRepository("SlackOAuthState")
        self.expiration_seconds = expiration_seconds

    @property
    def logger(self) -> logging.Logger:
        return logger

    async def async_issue(self, *args, **kwargs) -> str:
        state = str(uuid.uuid4())
        key = self.repo.get_key(state)
        entity = datastore.Entity(key=key)
        entity.update({"created_at": time.time()})
        self.repo.client.put(entity)
        return state

    async def async_consume(self, state: str) -> bool:
        key = self.repo.get_key(state)
        entity = self.repo.client.get(key)
        if entity:
            self.repo.delete(state)
            created_at = entity.get("created_at", 0)
            if time.time() - created_at <= self.expiration_seconds:
                return True
        return False


class DatastoreInstallationStore(AsyncInstallationStore):
    def __init__(self):
        self.installation_repo = DatastoreRepository(SlackInstallation.kind)
        self.bot_repo = DatastoreRepository(SlackBot.kind)

    @property
    def logger(self) -> logging.Logger:
        return logger

    async def async_save(self, installation: Installation):
        # Save bot information
        if installation.bot_token:
            await self.async_save_bot(installation.to_bot())

        # Save installation information
        key = self.installation_repo.get_key(
            f"{installation.team_id or ''}-{installation.user_id or ''}"
        )
        entity = datastore.Entity(key=key)

        # Use to_dict() if available or a custom one to ensure clean data
        data = {k: v for k, v in installation.__dict__.items() if v is not None}

        entity.update(data)
        self.installation_repo.client.put(entity)

    async def async_save_bot(self, bot: Bot):
        key = self.bot_repo.get_key(bot.team_id or "enterprise")
        entity = datastore.Entity(key=key)
        data = {k: v for k, v in bot.__dict__.items() if v is not None}
        entity.update(data)
        self.bot_repo.client.put(entity)

    async def async_find_bot(
        self,
        *,
        enterprise_id: str | None,
        team_id: str | None,
        is_enterprise_install: bool | None = False,
    ) -> Bot | None:
        key = self.bot_repo.get_key(team_id or "enterprise")
        entity = self.bot_repo.client.get(key)
        if entity:
            return Bot(**dict(entity))
        return None

    async def async_find_installation(
        self,
        *,
        enterprise_id: str | None,
        team_id: str | None,
        user_id: str | None = None,
        is_enterprise_install: bool | None = False,
    ) -> Installation | None:
        if user_id:
            key = self.installation_repo.get_key(f"{team_id or ''}-{user_id}")
            entity = self.installation_repo.client.get(key)
            if entity:
                return Installation(**dict(entity))
        return None

    async def async_delete_bot(
        self,
        *,
        enterprise_id: str | None,
        team_id: str | None,
    ) -> None:
        self.bot_repo.delete(team_id or "enterprise")

    async def async_delete_installation(
        self,
        *,
        enterprise_id: str | None,
        team_id: str | None,
        user_id: str | None = None,
    ) -> None:
        if user_id:
            self.installation_repo.delete(f"{team_id or ''}-{user_id}")
