import os
import sys
from unittest.mock import MagicMock

# Set dummy environment variables
os.environ["TG_TOKEN"] = "dummy_token"
os.environ["SLACK_CLIENT_ID"] = "dummy_id"
os.environ["SLACK_CLIENT_SECRET"] = "dummy_secret"
os.environ["MOD_CHAT_ID"] = "12345"
os.environ["OWNER_ID"] = "12345"
os.environ["GOOGLE_CLOUD_PROJECT"] = "dummy-project"
os.environ["BASE_URL"] = "http://localhost"
os.environ["TWITTER_CONSUMER_KEY"] = "dummy_key"
os.environ["TWITTER_CONSUMER_KEY_SECRET"] = "dummy_secret"

# Mock google.cloud.datastore
mock_datastore = MagicMock()
sys.modules["google.cloud.datastore"] = mock_datastore
# Mock google.cloud.storage
mock_storage = MagicMock()
sys.modules["google.cloud.storage"] = mock_storage

import pytest  # noqa: E402


@pytest.fixture
def mock_datastore_client():
    from utils import gcp

    client = MagicMock()
    mock_datastore.Client.return_value = client
    gcp._DATASTORE_CLIENT = None
    return client


@pytest.fixture
def client():
    from litestar.testing import TestClient
    from main import app

    with TestClient(app=app) as client:
        yield client


@pytest.fixture
def mock_container():
    from unittest.mock import patch, AsyncMock, PropertyMock
    from core.container import services

    with (
        patch(
            "core.container.Container.user_service", new_callable=PropertyMock
        ) as mock_user_service_prop,
        patch(
            "core.container.Container.usage_service", new_callable=PropertyMock
        ) as mock_usage_service_prop,
        patch(
            "core.container.Container.phrase_service", new_callable=PropertyMock
        ) as mock_phrase_service_prop,
        patch(
            "core.container.Container.badge_service", new_callable=PropertyMock
        ) as mock_badge_service_prop,
        patch(
            "core.container.Container.proposal_service", new_callable=PropertyMock
        ) as mock_proposal_service_prop,
        patch(
            "core.container.Container.ai_service", new_callable=PropertyMock
        ) as mock_ai_service_prop,
        patch(
            "core.container.Container.tts_service", new_callable=PropertyMock
        ) as mock_tts_service_prop,
        patch(
            "core.container.Container.cunhao_agent", new_callable=PropertyMock
        ) as mock_cunhao_agent_prop,
        patch.object(services, "user_repo") as mock_user_repo,
        patch.object(services, "chat_repo") as mock_chat_repo,
        patch.object(services, "phrase_repo") as mock_phrase_repo,
        patch.object(services, "long_phrase_repo") as mock_long_phrase_repo,
        patch.object(services, "proposal_repo") as mock_proposal_repo,
        patch.object(services, "long_proposal_repo") as mock_long_proposal_repo,
        patch.object(services, "usage_repo") as mock_usage_repo,
        patch.object(services, "gift_repo") as mock_gift_repo,
        patch.object(services, "link_request_repo") as mock_link_request_repo,
    ):
        mock_user_service = AsyncMock()
        mock_user_service_prop.return_value = mock_user_service

        mock_usage_service = AsyncMock()
        mock_usage_service_prop.return_value = mock_usage_service

        mock_phrase_service = AsyncMock()
        mock_phrase_service_prop.return_value = mock_phrase_service

        mock_badge_service = AsyncMock()
        mock_badge_service_prop.return_value = mock_badge_service

        mock_proposal_service = AsyncMock()
        mock_proposal_service_prop.return_value = mock_proposal_service

        mock_ai_service = AsyncMock()
        mock_ai_service_prop.return_value = mock_ai_service

        mock_tts_service = AsyncMock()
        mock_tts_service_prop.return_value = mock_tts_service

        mock_cunhao_agent = AsyncMock()
        mock_cunhao_agent_prop.return_value = mock_cunhao_agent

        yield {
            "user_service": mock_user_service,
            "usage_service": mock_usage_service,
            "phrase_service": mock_phrase_service,
            "badge_service": mock_badge_service,
            "proposal_service": mock_proposal_service,
            "ai_service": mock_ai_service,
            "tts_service": mock_tts_service,
            "cunhao_agent": mock_cunhao_agent,
            "user_repo": mock_user_repo,
            "chat_repo": mock_chat_repo,
            "phrase_repo": mock_phrase_repo,
            "long_phrase_repo": mock_long_phrase_repo,
            "proposal_repo": mock_proposal_repo,
            "long_proposal_repo": mock_long_proposal_repo,
            "usage_repo": mock_usage_repo,
            "gift_repo": mock_gift_repo,
            "link_request_repo": mock_link_request_repo,
        }
