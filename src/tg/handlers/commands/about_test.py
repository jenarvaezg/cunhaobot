import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.about import handle_about
from models.phrase import Phrase


@pytest.mark.asyncio
async def test_handle_about():
    update = MagicMock()
    message = MagicMock()
    user = MagicMock()

    user.id = 12345
    user.name = "Test User"
    user.username = "test_user"

    message.reply_text = AsyncMock()
    message.chat.title = "Test Chat"
    message.chat.PRIVATE = "private"
    message.chat.type = "group"
    message.chat_id = 1

    update.effective_message = message
    update.effective_user = user

    context = MagicMock()

    mock_phrase = Phrase(text="cuñao")
    with patch("tg.handlers.commands.about.services") as mock_services:
        mock_services.user_service.update_or_create_user = AsyncMock()
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])
        mock_services.phrase_service.get_random = AsyncMock(return_value=mock_phrase)

        await handle_about(update, context)
        update.effective_message.reply_text.assert_called_once()
