import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.about import handle_about
from models.phrase import Phrase


@pytest.mark.asyncio
async def test_handle_about():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.effective_message.chat.title = "Test Chat"
    update.effective_message.chat.PRIVATE = "private"
    update.effective_message.chat.type = "group"
    update.effective_user.id = 12345
    update.effective_user.name = "Test User"
    update.effective_user.username = "test_user"
    update.effective_message.chat_id = 1
    context = MagicMock()

    mock_phrase = Phrase(text="cuñao")
    with patch("tg.handlers.commands.about.services") as mock_services:
        mock_services.user_service.update_or_create_user = AsyncMock()
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])
        mock_services.phrase_service.get_random = AsyncMock(return_value=mock_phrase)

        await handle_about(update, context)
        update.effective_message.reply_text.assert_called_once()
