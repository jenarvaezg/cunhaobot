import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.cancel import handle_cancel


@pytest.mark.asyncio
async def test_handle_cancel():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    with patch("models.phrase.Phrase.get_random_phrase", return_value="cuñao"):
        await handle_cancel(update, context)
        update.effective_message.reply_text.assert_called_once()
