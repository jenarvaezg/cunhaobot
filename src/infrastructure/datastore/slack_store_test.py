import time
from unittest.mock import MagicMock, patch

import pytest
from slack_sdk.oauth.installation_store import Installation

from infrastructure.datastore.slack_store import (
    DatastoreInstallationStore,
    DatastoreOAuthStateStore,
)


class TestSlackStore:
    @pytest.fixture
    def mock_client(self):
        with (
            patch(
                "infrastructure.datastore.base.get_datastore_client"
            ) as mock_get_client,
            patch("google.cloud.datastore.Client"),
            patch("google.cloud.datastore.Entity") as mock_entity,
        ):
            mock_client_instance = MagicMock()
            mock_get_client.return_value = mock_client_instance
            yield mock_client_instance, mock_entity

    @pytest.mark.asyncio
    async def test_state_store_issue_consume(self, mock_client):
        client, entity_cls = mock_client
        store = DatastoreOAuthStateStore(expiration_seconds=60)

        # Test issue
        state = await store.async_issue()
        assert state is not None
        client.put.assert_called_once()

        # Test consume success
        mock_entity_instance = MagicMock()
        mock_entity_instance.get.return_value = time.time()
        client.get.return_value = mock_entity_instance

        success = await store.async_consume(state)
        assert success is True
        client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_installation_store_save_find(self, mock_client):
        client, entity_cls = mock_client
        store = DatastoreInstallationStore()

        installation = Installation(
            app_id="app",
            enterprise_id="ent",
            team_id="team",
            user_id="user",
            bot_token="xoxb-token",
            bot_id="bot",
            bot_user_id="bot-user",
        )

        # Test save
        await store.async_save(installation)
        assert client.put.call_count == 2  # Bot and Installation

        # Test find bot
        client.get.return_value = {
            "bot_token": "xoxb-token",
            "bot_id": "bot",
            "bot_user_id": "bot-user",
            "team_id": "team",
        }
        bot = await store.async_find_bot(enterprise_id="ent", team_id="team")
        assert bot is not None
        assert bot.bot_token == "xoxb-token"

        # Test find installation
        client.get.return_value = {
            "app_id": "app",
            "team_id": "team",
            "user_id": "user",
            "bot_token": "xoxb-token",
        }
        inst = await store.async_find_installation(
            enterprise_id="ent", team_id="team", user_id="user"
        )
        assert inst is not None
        assert inst.user_id == "user"
