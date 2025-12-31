import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from models.user import User


@pytest.fixture
def mock_users():
    return [
        User(id=1, name="User 1", platform="telegram", gdpr=False),
        User(id=2, name="User 2", platform="telegram", gdpr=False),
        User(id=3, name="Group 1", platform="telegram", gdpr=False, is_group=True),
        User(id="slack1", name="Slack 1", platform="slack", gdpr=False),
    ]


def test_get_broadcast_owner(client):
    with patch("core.config.config.is_gae", False):
        rv = client.get("/admin/broadcast")
        assert rv.status_code == 200
        assert b"Broadcast Maestro" in rv.content


def test_post_broadcast_success(client, mock_users):
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch(
            "services.user_service.user_service.user_repo.load_all",
            return_value=mock_users,
        ),
        patch("services.user_service.user_service.user_repo.save") as mock_save,
        patch("tg.get_tg_application", return_value=mock_app),
    ):
        rv = client.post("/admin/broadcast", data={"message": "Hola caracola"})
        assert rv.status_code == 200

        # Should have sent 2 messages (User 1 and User 2, not Group 1, not Slack 1)
        assert mock_bot.send_message.call_count == 2
        mock_save.assert_not_called()
        assert b"2 enviados" in rv.content


def test_post_broadcast_with_errors(client, mock_users):
    mock_bot = AsyncMock()
    # User 1 succeeds, User 2 fails
    mock_bot.send_message.side_effect = [None, Exception("Failed")]
    mock_app = MagicMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch(
            "services.user_service.user_service.user_repo.load_all",
            return_value=mock_users,
        ),
        patch("services.user_service.user_service.user_repo.save") as mock_save,
        patch("tg.get_tg_application", return_value=mock_app),
    ):
        rv = client.post("/admin/broadcast", data={"message": "Hola caracola"})
        assert rv.status_code == 200

        assert mock_bot.send_message.call_count == 2
        # One user should have been saved with gdpr=True
        assert mock_save.call_count == 1
        saved_user = mock_save.call_args[0][0]
        assert saved_user.id == 2
        assert saved_user.gdpr is True

        assert b"1 enviados" in rv.content
        assert b"1 fallidos" in rv.content
