import pytest
from unittest.mock import AsyncMock, patch
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
from litestar.testing import TestClient
import hashlib

from main import app
from core.config import config


@pytest.fixture
def client():
    with TestClient(app=app) as client:
        yield client


def test_game_launch(client):
    response = client.get(
        "/game/launch", params={"user_id": "123", "inline_message_id": "abc"}
    )
    assert response.status_code == HTTP_200_OK
    assert "Paco's Tapas Runner" in response.text
    # Check for the USER_ID initialization in script tag
    assert 'const USER_ID = "123";' in response.text


@pytest.mark.asyncio
async def test_submit_score_success(client):
    import hmac
    import time

    user_id = "123"
    score = 500

    timestamp = int(time.time())
    token_payload = f"{user_id}:{timestamp}"
    signature = hmac.new(
        config.session_secret.encode(), token_payload.encode(), hashlib.sha256
    ).hexdigest()
    token = f"{signature}:{timestamp}"

    payload = {
        "user_id": user_id,
        "score": score,
        "inline_message_id": "abc",
        "token": token,
    }

    # We need to override dependencies in Litestar for clean testing
    # But since the project uses patch heavily, let's patch the service methods
    with (
        patch(
            "services.game_service.GameService.set_score", new_callable=AsyncMock
        ) as mock_set_score,
        patch(
            "services.user_service.UserService.add_points", new_callable=AsyncMock
        ) as mock_add_points,
    ):
        mock_set_score.return_value = True

        response = client.post("/game/score", json=payload)

        assert response.status_code == HTTP_201_CREATED
        assert response.json() == {"status": "ok", "success": True}

        mock_set_score.assert_called_once_with(
            user_id="123",
            score=500,
            inline_message_id="abc",
            chat_id=None,
            message_id=None,
        )
        # points = int(500 / 100) = 5
        mock_add_points.assert_called_once_with("123", 5)
