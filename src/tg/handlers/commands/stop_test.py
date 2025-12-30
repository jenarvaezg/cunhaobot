import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.stop import handle_stop
from models.user import User
from telegram import Chat
from services.user_service import UserService


@pytest.mark.asyncio
async def test_handle_stop():
    update = MagicMock()
    update.to_dict.return_value = {"update_id": 1}
    update.effective_user.id = 123
    update.effective_user.name = "testuser"
    update.effective_chat.id = 456
    update.effective_chat.type = Chat.PRIVATE
    update.effective_chat.PRIVATE = Chat.PRIVATE
    update.effective_message.chat_id = 456
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    mock_user = User(chat_id=456, name="testuser")
    mock_phrase = MagicMock()
    mock_phrase.text = "cuñao"

    with (
        patch("tg.handlers.commands.stop.user_repo.load", return_value=mock_user),
        patch("tg.handlers.commands.stop.user_service.delete_user") as mock_delete,
        patch("tg.handlers.commands.stop.schedule_repo.get_schedules", return_value=[]),
        patch(
            "tg.handlers.commands.stop.phrase_service.get_random",
            return_value=mock_phrase,
        ),
        patch.object(
            UserService, "update_or_create_user"
        ),  # Patch the method on the class
    ):
        await handle_stop(update, context)
        mock_delete.assert_called_once_with(mock_user)
        update.effective_message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_stop_with_chapas():
    update = MagicMock()
    update.to_dict.return_value = {"update_id": 1}
    update.effective_user.id = 123
    update.effective_user.name = "testuser"
    update.effective_chat.id = 456
    update.effective_chat.type = Chat.PRIVATE
    update.effective_chat.PRIVATE = Chat.PRIVATE
    update.effective_message.chat_id = 456
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    mock_task = MagicMock()
    mock_task.id = "task123"
    mock_phrase = MagicMock()
    mock_phrase.text = "cuñao"

    with (
        patch("tg.handlers.commands.stop.user_repo.load", return_value=None),
        patch(
            "tg.handlers.commands.stop.schedule_repo.get_schedules",
            return_value=[mock_task],
        ),
        patch("tg.handlers.commands.stop.schedule_repo.delete") as mock_delete_task,
        patch(
            "tg.handlers.commands.stop.phrase_service.get_random",
            return_value=mock_phrase,
        ),
        patch.object(
            UserService, "update_or_create_user"
        ),  # Patch the method on the class
    ):
        await handle_stop(update, context)
        mock_delete_task.assert_called_once_with("task123")
        update.effective_message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_stop_no_user():
    update = MagicMock()
    update.effective_user = None
    update.effective_chat.type = (
        Chat.PRIVATE
    )  # Ensure chat type is set for _get_name_from_message
    update.effective_message = None  # No message, so update_or_create_user returns None
    context = MagicMock()
    with patch.object(
        UserService, "update_or_create_user"
    ) as mock_update_or_create:  # Patch the method on the class
        await handle_stop(update, context)
        mock_update_or_create.assert_called_once_with(update)
