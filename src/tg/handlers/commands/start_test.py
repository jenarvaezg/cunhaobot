import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.start import handle_start


@pytest.mark.asyncio
async def test_handle_start():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.to_dict.return_value = {}
    context = MagicMock()

    mock_phrase1 = MagicMock()
    mock_phrase1.text = "cuñao"

    with patch("tg.handlers.commands.start.services") as mock_services:
        mock_services.phrase_service.get_random = AsyncMock(return_value=mock_phrase1)
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])
        mock_services.user_service.update_or_create_user = AsyncMock()

        await handle_start(update, context)

    # Check reply
    update.effective_message.reply_text.assert_called_once()
    args, _ = update.effective_message.reply_text.call_args
    msg = args[0]
    assert "cuñao" in msg
    assert "Bienvenido" in msg
    assert "/perfil" in msg
    assert "@cunhaobot" in msg
