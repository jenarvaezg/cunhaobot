import pytest
from unittest.mock import MagicMock, AsyncMock, patch
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
    assert 'USER_ID = "123"' in response.text


@pytest.mark.asyncio
async def test_submit_score_success(client):
    user_id = "123"
    score = 500
    hash_val = hashlib.sha256(
        f"{user_id}{score}{config.session_secret}".encode()
    ).hexdigest()

    payload = {
        "user_id": user_id,
        "score": score,
        "inline_message_id": "abc",
        "hash": hash_val,
    }

    mock_user = MagicMock()
    mock_user.points = 1000
    mock_user.game_stats = 0
    mock_user.game_streak = 0
    mock_user.game_high_score = 0
    mock_user.last_game_at = None
    mock_user.platform = "telegram"

    with (
        patch("api.game.UserRepository"),
        patch("api.game.get_tg_application") as mock_tg_app,
        patch(
            "infrastructure.datastore.user.user_repository.load", new_callable=AsyncMock
        ) as mock_load,
        patch(
            "infrastructure.datastore.user.user_repository.save", new_callable=AsyncMock
        ) as mock_save,
        patch(
            "services.badge_service.badge_service.check_badges", new_callable=AsyncMock
        ) as mock_badges,
    ):
        mock_load.return_value = mock_user
        mock_bot = AsyncMock()
        mock_tg_app.return_value.bot = mock_bot
        mock_tg_app.return_value.running = True

        response = client.post("/game/score", json=payload)

        assert response.status_code == HTTP_201_CREATED
        assert response.json() == {"status": "ok"}
        assert mock_user.points == 1005
        assert mock_user.game_stats == 1
        assert mock_user.game_streak == 1
        assert mock_user.game_high_score == 500
        mock_save.assert_called_once_with(mock_user)
        mock_bot.set_game_score.assert_called_once_with(
            user_id=123, score=500, inline_message_id="abc"
        )
        mock_badges.assert_called_once_with("123", "telegram")
