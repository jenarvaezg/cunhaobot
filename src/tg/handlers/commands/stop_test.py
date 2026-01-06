import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.stop import handle_stop
from models.user import User
from telegram import Chat


@pytest.mark.asyncio
async def test_handle_stop():
    update = MagicMock()
    update.to_dict.return_value = {"update_id": 1}
    update.effective_user.id = 123
    update.effective_user.name = "testuser"
    update.effective_user.username = "testuser"
    update.effective_chat.id = 456
    update.effective_chat.type = Chat.PRIVATE
    update.effective_chat.title = "Chat"
    update.effective_chat.PRIVATE = Chat.PRIVATE
    update.effective_message.chat_id = 456
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    mock_user = User(id=456, name="testuser")
    mock_phrase = MagicMock()
    mock_phrase.text = "cuñao"

    with patch("tg.handlers.commands.stop.services") as mock_services:
        mock_services.user_repo.load = AsyncMock(return_value=mock_user)
        mock_services.user_service.delete_user = AsyncMock()
        mock_services.phrase_service.get_random = AsyncMock(return_value=mock_phrase)
        mock_services.user_service.update_or_create_user = AsyncMock()

        await handle_stop(update, context)
        mock_services.user_service.delete_user.assert_called_once_with(mock_user)
        update.effective_message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_stop_no_user():
    update = MagicMock()
    update.effective_user = None
    update.effective_chat.type = Chat.PRIVATE
    update.effective_message = None
    context = MagicMock()
    await handle_stop(update, context)
