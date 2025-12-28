import pytest
from unittest.mock import MagicMock, AsyncMock
from tg.handlers.commands.about import handle_about


@pytest.mark.asyncio
async def test_handle_about():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    await handle_about(update, context)
    update.effective_message.reply_text.assert_called_once()
