import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Message, User, CallbackQuery
from tg.handlers.commands.gift import handle_gift_command, handle_gift_selection


@pytest.mark.asyncio
async def test_handle_gift_command_no_reply():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    message.reply_to_message = None

    # User mock
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "sender"
    user.first_name = "Sender"
    user.name = "Sender"
    user.is_bot = False
    message.from_user = user
    update.effective_user = user

    # Chat mock
    chat = MagicMock()
    chat.type = "private"
    chat.title = None
    chat.username = "privatechat"
    message.chat = chat
    update.effective_chat = chat

    message.reply_text = AsyncMock()
    context = MagicMock()

    await handle_gift_command(update, context)

    message.reply_text.assert_called_once()
    assert "responde a un mensaje" in message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_gift_command_success():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    message.reply_to_message = MagicMock(spec=Message)

    # Receiver mock
    receiver = MagicMock(spec=User)
    receiver.id = 2
    receiver.first_name = "Receiver"
    receiver.username = "receiver"
    receiver.is_bot = False
    message.reply_to_message.from_user = receiver

    # Sender mock
    sender = MagicMock(spec=User)
    sender.id = 1
    sender.first_name = "Sender"
    sender.username = "sender"
    sender.name = "Sender"
    sender.is_bot = False
    message.from_user = sender
    update.effective_user = sender

    # Chat mock
    chat = MagicMock()
    chat.type = "group"
    chat.title = "Test Group"
    chat.username = None
    message.chat = chat
    update.effective_chat = chat

    message.reply_text = AsyncMock()
    context = MagicMock()

    await handle_gift_command(update, context)

    message.reply_text.assert_called_once()
    assert "Receiver" in message.reply_text.call_args[0][0]
    assert message.reply_text.call_args[1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_gift_selection_success():
    update = MagicMock(spec=Update)
    query = MagicMock(spec=CallbackQuery)
    update.callback_query = query
    query.data = "gift_sel:2:carajillo"

    # Query user mock
    user = MagicMock(spec=User)
    user.id = 1
    user.first_name = "Sender"
    user.username = "sender"
    user.name = "Sender"
    user.is_bot = False
    query.from_user = user
    update.effective_user = user

    # Query message mock
    q_message = MagicMock(spec=Message)
    q_message.chat_id = 123

    # Chat mock
    chat = MagicMock()
    chat.type = "private"
    chat.title = None
    chat.username = "privatechat"
    q_message.chat = chat
    update.effective_chat = chat

    query.message = q_message
    update.effective_message = q_message

    context = MagicMock()
    context.bot.send_invoice = AsyncMock()

    await handle_gift_selection(update, context)

    query.answer.assert_called_once()
    context.bot.send_invoice.assert_called_once()
    assert context.bot.send_invoice.call_args[1]["payload"] == "gift:2:carajillo"
