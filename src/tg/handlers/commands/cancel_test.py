import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.cancel import handle_cancel


@pytest.mark.asyncio
async def test_handle_cancel():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    mock_phrase = MagicMock()
    mock_phrase.text = "cuñao"

    with (
        patch("tg.handlers.commands.cancel.services") as mock_services,
        patch("tg.decorators.services") as mock_decorator_services,
    ):
        mock_services.phrase_service.get_random = AsyncMock(return_value=mock_phrase)
        mock_decorator_services.user_service.update_or_create_user = AsyncMock()
        await handle_cancel(update, context)
        update.effective_message.reply_text.assert_called_once()
        args, _ = update.effective_message.reply_text.call_args
        assert "Pues vale, cuñao." in args[0]
