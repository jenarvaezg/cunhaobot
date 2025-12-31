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


@pytest.mark.asyncio
async def test_broadcast_page_unauthorized(client):
    # Test without being the owner
    with patch(
        "core.config.config.is_gae", True
    ):  # Force it to not auto-login as owner
        response = client.get("/admin/broadcast")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_broadcast_page_success(client):
    # Test as owner (auto-login in local dev)
    with patch("core.config.config.is_gae", False):
        response = client.get("/admin/broadcast")
        assert response.status_code == 200
        assert b"BROADCAST MAESTRO" in response.content


@pytest.mark.asyncio
async def test_broadcast_send_text_success(client, mock_users):
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch(
            "infrastructure.datastore.user.UserDatastoreRepository.load_all",
            return_value=mock_users,
        ),
        patch("api.admin.get_tg_application", return_value=mock_app),
    ):
        response = client.post("/admin/broadcast", data={"message": "Hola caracola"})
        assert response.status_code == 200

        # Should have sent 2 messages (User 1 and User 2, not Group 1, not Slack 1)
        assert mock_bot.send_message.call_count == 2
        assert b"2 enviados" in response.content


@pytest.mark.asyncio
async def test_broadcast_send_image_success(client):
    mock_user = User(id=123, name="Test Machine", platform="telegram", gdpr=False)

    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch(
            "infrastructure.datastore.user.UserDatastoreRepository.load_all",
            return_value=[mock_user],
        ),
        patch("api.admin.get_tg_application", return_value=mock_app),
    ):
        # Prepare a dummy file upload
        files = {"data": ("test.png", b"fake-image-bytes", "image/png")}

        response = client.post(
            "/admin/broadcast", files=files, data={"message": "Optional caption"}
        )

        assert response.status_code == 200
        assert b"1 enviados" in response.content
        mock_bot.send_photo.assert_called_once_with(
            chat_id=123, photo=b"fake-image-bytes", caption="Optional caption"
        )


@pytest.mark.asyncio
async def test_broadcast_send_video_success(client):
    mock_user = User(id=123, name="Test Machine", platform="telegram", gdpr=False)

    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch(
            "infrastructure.datastore.user.UserDatastoreRepository.load_all",
            return_value=[mock_user],
        ),
        patch("api.admin.get_tg_application", return_value=mock_app),
    ):
        # Prepare a dummy video upload
        files = {"data": ("test.mp4", b"fake-video-bytes", "video/mp4")}

        response = client.post("/admin/broadcast", files=files)

        assert response.status_code == 200
        assert b"1 enviados" in response.content
        mock_bot.send_video.assert_called_once_with(
            chat_id=123, video=b"fake-video-bytes", caption=None
        )


@pytest.mark.asyncio
async def test_broadcast_send_skips_non_telegram(client):
    mock_user_tg = User(id=123, name="TG User", platform="telegram", gdpr=False)
    mock_user_slack = User(id="S456", name="Slack User", platform="slack", gdpr=False)

    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch(
            "infrastructure.datastore.user.UserDatastoreRepository.load_all",
            return_value=[mock_user_tg, mock_user_slack],
        ),
        patch("api.admin.get_tg_application", return_value=mock_app),
    ):
        response = client.post("/admin/broadcast", data={"message": "Skip slack"})

        assert response.status_code == 200
        assert b"1 enviados" in response.content
        mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_broadcast_send_failure_updates_gdpr(client):
    mock_user = User(id=123, name="Test Machine", platform="telegram", gdpr=False)

    mock_bot = AsyncMock()
    # Fail the send_message call
    mock_bot.send_message.side_effect = Exception("Telegram Error")
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch(
            "infrastructure.datastore.user.UserDatastoreRepository.load_all",
            return_value=[mock_user],
        ),
        patch(
            "infrastructure.datastore.user.UserDatastoreRepository.save"
        ) as mock_save,
        patch("api.admin.get_tg_application", return_value=mock_app),
    ):
        response = client.post("/admin/broadcast", data={"message": "fail"})

        assert response.status_code == 200
        assert b"1 fallidos" in response.content
        # Should have updated GDPR to True
        mock_save.assert_called_once()
        saved_user = mock_save.call_args[0][0]
        assert saved_user.id == 123
        assert saved_user.gdpr is True
