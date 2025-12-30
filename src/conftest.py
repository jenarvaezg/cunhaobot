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
    return mock_datastore.Client.return_value


@pytest.fixture
def client():
    from litestar.testing import TestClient
    from main import app

    with TestClient(app=app) as client:
        yield client
