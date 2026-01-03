import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, Message
from tg.handlers.commands.poster import handle_poster


@pytest.mark.asyncio
async def test_handle_poster_no_args():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_user.id = 123
    update.effective_chat.type = "private"
    update.effective_chat.title = "Test Chat"
    update.effective_chat.username = "testchat"
    message.chat.type = "private"
    message.chat.title = "Test Chat"
    message.chat.username = "testchat"
    message.chat_id = 123

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
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_user.id = 123
    update.effective_chat.type = "private"
    update.effective_chat.title = "Test Chat"
    update.effective_chat.username = "testchat"
    message.chat.type = "private"
    message.chat.title = "Test Chat"
    message.chat.username = "testchat"
    message.chat_id = 123

    message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["a"] * 201

    await handle_poster(update, context)

    message.reply_text.assert_called_once()
    assert "más larga que un día sin pan" in message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_poster_success_non_owner():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    update.effective_user.id = 999  # Not the owner
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Test Chat"
    update.effective_chat.username = "testchat"
    message.chat.type = "private"
    message.chat.title = "Test Chat"
    message.chat.username = "testchat"
    message.chat_id = 999

    message.reply_invoice = AsyncMock()
    context = MagicMock()
    context.args = ["El", "futuro", "es", "el", "diésel"]

    with patch("tg.handlers.commands.poster.config") as mock_config:
        mock_config.owner_id = "123"
        await handle_poster(update, context)

    message.reply_invoice.assert_called_once()
    call_kwargs = message.reply_invoice.call_args[1]
    assert call_kwargs["prices"][0].amount == 50


@pytest.mark.asyncio
async def test_handle_poster_success_owner():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    update.effective_user.id = "123"  # The owner
    update.effective_user.name = "Owner"
    update.effective_user.username = "owner"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Owner Chat"
    update.effective_chat.username = "ownerchat"
    message.chat.type = "private"
    message.chat.title = "Owner Chat"
    message.chat.username = "ownerchat"
    message.chat_id = 123

    message.reply_invoice = AsyncMock()
    context = MagicMock()
    context.args = ["El", "futuro", "es", "el", "diésel"]

    with patch("tg.handlers.commands.poster.config") as mock_config:
        mock_config.owner_id = "123"
        await handle_poster(update, context)

    message.reply_invoice.assert_called_once()
    call_kwargs = message.reply_invoice.call_args[1]
    assert call_kwargs["prices"][0].amount == 1
