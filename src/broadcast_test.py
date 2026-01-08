import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from models.user import User
from models.chat import Chat


@pytest.fixture
def mock_users():
    return [
        User(id=1, name="User 1", platform="telegram", gdpr=False),
        User(id=2, name="User 2", platform="telegram", gdpr=False),
        User(id="slack1", name="Slack 1", platform="slack", gdpr=False),
    ]


@pytest.fixture
def mock_chats():
    return [
        Chat(id=1, title="Chat 1", type="private", platform="telegram"),
        Chat(id=2, title="Chat 2", type="private", platform="telegram"),
        Chat(id=3, title="Group 1", type="group", platform="telegram"),
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
    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.allow_local_login", True),
    ):
        response = client.get("/admin/broadcast")
        assert response.status_code == 200
        assert b"BROADCAST MAESTRO" in response.content


@pytest.mark.asyncio
async def test_broadcast_send_text_success(client, mock_users, mock_chats):
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.allow_local_login", True),
        patch(
            "infrastructure.datastore.user.UserDatastoreRepository.load_all",
            return_value=mock_users,
        ),
        patch(
            "infrastructure.datastore.chat.ChatDatastoreRepository.load_all",
            return_value=mock_chats,
        ),
        patch(
            "api.admin.get_initialized_tg_application",
            new_callable=AsyncMock,
            return_value=mock_app,
        ),
    ):
        response = client.post("/admin/broadcast", data={"message": "Hola caracola"})
        assert response.status_code == 200

        # By default, it sends only to private chats (Chat 1 and Chat 2)
        # mock_chats has 2 private, 1 group.
        assert mock_bot.send_message.call_count == 2
        assert b"2 enviados" in response.content


@pytest.mark.asyncio
async def test_broadcast_send_image_success(client, mock_chats):
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.allow_local_login", True),
        patch(
            "infrastructure.datastore.chat.ChatDatastoreRepository.load_all",
            # Just one private chat for this test
            return_value=[mock_chats[0]],
        ),
        patch(
            "api.admin.get_initialized_tg_application",
            new_callable=AsyncMock,
            return_value=mock_app,
        ),
    ):
        # Prepare a dummy file upload
        files = {"data": ("test.png", b"fake-image-bytes", "image/png")}

        response = client.post(
            "/admin/broadcast", files=files, data={"message": "Optional caption"}
        )

        assert response.status_code == 200
        assert b"1 enviados" in response.content
        mock_bot.send_photo.assert_called_once_with(
            chat_id=1, photo=b"fake-image-bytes", caption="Optional caption"
        )


@pytest.mark.asyncio
async def test_broadcast_send_video_success(client, mock_chats):
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.allow_local_login", True),
        patch(
            "infrastructure.datastore.chat.ChatDatastoreRepository.load_all",
            return_value=[mock_chats[0]],
        ),
        patch(
            "api.admin.get_initialized_tg_application",
            new_callable=AsyncMock,
            return_value=mock_app,
        ),
    ):
        # Prepare a dummy video upload
        files = {"data": ("test.mp4", b"fake-video-bytes", "video/mp4")}

        response = client.post("/admin/broadcast", files=files)

        assert response.status_code == 200
        assert b"1 enviados" in response.content
        mock_bot.send_video.assert_called_once_with(
            chat_id=1, video=b"fake-video-bytes", caption=""
        )


@pytest.mark.asyncio
async def test_broadcast_send_skips_inactive(client, mock_chats):
    mock_chats[0].is_active = False

    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.allow_local_login", True),
        patch(
            "infrastructure.datastore.chat.ChatDatastoreRepository.load_all",
            return_value=mock_chats,
        ),
        patch(
            "api.admin.get_initialized_tg_application",
            new_callable=AsyncMock,
            return_value=mock_app,
        ),
    ):
        response = client.post("/admin/broadcast", data={"message": "Skip inactive"})

        assert response.status_code == 200
        # Only Chat 2 should receive it (Chat 1 is inactive, Chat 3 is group)
        assert mock_bot.send_message.call_count == 1


@pytest.mark.asyncio
async def test_broadcast_send_failure_updates_active(client, mock_chats):
    mock_bot = AsyncMock()
    # Fail the send_message call
    mock_bot.send_message.side_effect = Exception("Telegram Error")
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.allow_local_login", True),
        patch(
            "infrastructure.datastore.chat.ChatDatastoreRepository.load_all",
            return_value=[mock_chats[0]],
        ),
        patch(
            "infrastructure.datastore.chat.ChatDatastoreRepository.save"
        ) as mock_save,
        patch(
            "api.admin.get_initialized_tg_application",
            new_callable=AsyncMock,
            return_value=mock_app,
        ),
    ):
        response = client.post("/admin/broadcast", data={"message": "fail"})

        assert response.status_code == 200
        assert b"0 enviados" in response.content
        # Should have updated is_active to False
        mock_save.assert_called_once()
        saved_chat = mock_save.call_args[0][0]
        assert saved_chat.id == 1
        assert saved_chat.is_active is False


@pytest.mark.asyncio
async def test_broadcast_status_sse_success(client, mock_chats):
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.bot = mock_bot

    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.allow_local_login", True),
        patch(
            "infrastructure.datastore.chat.ChatDatastoreRepository.load_all",
            return_value=mock_chats,
        ),
        patch(
            "api.admin.get_initialized_tg_application",
            new_callable=AsyncMock,
            return_value=mock_app,
        ),
    ):
        # We use a GET request for SSE
        response = client.get("/admin/broadcast/status", params={"message": "SSE test"})

        assert response.status_code == 200
        # Check that it returns SSE content type
        assert "text/event-stream" in response.headers["content-type"]

        # Verify it sent messages to the 2 private telegram chats
        assert mock_bot.send_message.call_count == 2
