import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.help import handle_help


@pytest.mark.asyncio
async def test_handle_help():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    with (
        patch("models.phrase.Phrase.get_random_phrase", return_value="cuñao"),
        patch("models.phrase.LongPhrase.get_random_phrase", return_value="frase"),
    ):
        await handle_help(update, context)
        update.effective_message.reply_text.assert_called_once()
