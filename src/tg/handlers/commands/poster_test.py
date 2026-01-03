import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Message
from tg.handlers.commands.poster import handle_poster


@pytest.mark.asyncio
async def test_handle_poster_no_args():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = []

    await handle_poster(update, context)

    message.reply_text.assert_called_once()
    assert "Tienes que decirme qué frase quieres" in message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_poster_too_long():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["a"] * 201

    await handle_poster(update, context)

    message.reply_text.assert_called_once()
    assert "más larga que un día sin pan" in message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_poster_success():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    message.reply_invoice = AsyncMock()
    context = MagicMock()
    context.args = ["El", "futuro", "es", "el", "diésel"]

    await handle_poster(update, context)

    message.reply_invoice.assert_called_once()
    call_kwargs = message.reply_invoice.call_args[1]
    assert call_kwargs["title"] == "Poster Cuñao IA"
    assert call_kwargs["payload"] == "El futuro es el diésel"
    assert call_kwargs["currency"] == "XTR"
    assert call_kwargs["prices"][0].amount == 50
