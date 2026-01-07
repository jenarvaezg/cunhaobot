import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.help import handle_help


@pytest.mark.asyncio
async def test_handle_help():
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    mock_phrase1 = MagicMock()
    mock_phrase1.text = "cuñao"

    with patch("tg.handlers.commands.help.services") as mock_services:
        mock_services.phrase_service.get_random = AsyncMock(return_value=mock_phrase1)
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])
        mock_services.user_service.update_or_create_user = AsyncMock()

        await handle_help(update, context)
        update.effective_message.reply_text.assert_called_once()
        args, _ = update.effective_message.reply_text.call_args
        msg = args[0]
        assert "Cuñao Vision" in msg
        assert "/poster" in msg
        assert "/perfil" in msg
        assert "@cunhaobot" in msg
