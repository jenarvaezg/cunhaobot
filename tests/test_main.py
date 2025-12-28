import asyncio
import json
import os
from unittest.mock import MagicMock, patch

import pytest

# Import app from main
from main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_ping(client):
    rv = client.get("/")
    assert rv.data == b"I am alive"


def test_telegram_handler(client):
    token = os.environ["TG_TOKEN"]

    with patch("main.get_tg_application") as mock_get_app:
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_app.bot = MagicMock()

        # Mock initialize as async
        mock_app.initialize = MagicMock(return_value=asyncio.Future())
        mock_app.initialize.return_value.set_result(None)

        # Mock process_update as async
        mock_app.process_update = MagicMock(return_value=asyncio.Future())
        mock_app.process_update.return_value.set_result(None)

        with patch("telegram.Update.de_json") as mock_de_json:
            mock_update = MagicMock()
            mock_de_json.return_value = mock_update

            rv = client.post(f"/{token}", json={"update_id": 123})

            assert rv.data == b"Handled"
            mock_de_json.assert_called()
            mock_app.initialize.assert_called()
            mock_app.process_update.assert_called_with(mock_update)


def test_telegram_ping_handler(client):
    token = os.environ["TG_TOKEN"]

    with patch("main.get_tg_application") as mock_get_app:
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_app.bot = MagicMock()

        # Mock initialize as async
        mock_app.initialize = MagicMock(return_value=asyncio.Future())
        mock_app.initialize.return_value.set_result(None)

        with patch("main.handle_telegram_ping") as mock_ping:
            mock_ping.return_value = asyncio.Future()
            mock_ping.return_value.set_result(None)

            rv = client.get(f"/{token}/ping")

            assert rv.data == b"OK"
            mock_app.initialize.assert_called()
            mock_ping.assert_called_with(mock_app.bot)


def test_slack_handler_direct(client):
    with patch("main.handle_slack") as mock_handle_slack:
        # Mock response from slack handler
        mock_handle_slack.return_value = {
            "direct": "direct_response",
            "indirect": "indirect_payload",
        }

        with patch("requests.post") as mock_post:
            # Slack sends payload as form data string
            data = {
                "payload": json.dumps({"response_url": "http://slack.com/response"})
            }
            rv = client.post("/slack", data=data)

            assert rv.data == b"direct_response"
            mock_post.assert_called_with(
                "http://slack.com/response", json="indirect_payload"
            )


def test_slack_handler_no_response(client):
    with patch("main.handle_slack") as mock_handle_slack:
        mock_handle_slack.return_value = None

        data = {"payload": json.dumps({})}
        rv = client.post("/slack", data=data)

        assert rv.data == b""


def test_slack_auth(client):
    rv = client.get("/slack/auth")
    assert rv.status_code == 302
    assert "slack.com/oauth/v2/authorize" in rv.location


def test_slack_auth_redirect(client):
    with patch("requests.post") as mock_post:
        rv = client.get("/slack/auth/redirect?code=123")
        assert rv.data == b":)"
        mock_post.assert_called()


def test_twitter_auth_redirect(client):
    rv = client.get("/twitter/auth/redirect")
    assert rv.data == b":)"


def test_twitter_ping(client):
    with patch("tweepy.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        with patch("models.phrase.LongPhrase.get_random_phrase") as mock_phrase:
            mock_phrase.return_value.text = "tweet text"

            rv = client.get("/twitter/ping")

            assert rv.data == b""
            mock_client.create_tweet.assert_called_with(text="tweet text")
