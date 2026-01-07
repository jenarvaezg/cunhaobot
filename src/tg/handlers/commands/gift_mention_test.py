import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, Message, User, MessageEntity
from tg.handlers.commands.gift import handle_gift_command


@pytest.mark.asyncio
async def test_handle_gift_command_text_mention():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    message.reply_to_message = None

    # Sender
    sender = MagicMock(spec=User)
    sender.id = 1
    sender.first_name = "Sender"
    sender.name = "Sender"
    sender.username = "sender"
    message.from_user = sender
    update.effective_user = sender

    # Receiver (Text Mention)
    receiver = MagicMock(spec=User)
    receiver.id = 2
    receiver.first_name = "Receiver"
    receiver.username = "receiver"
    receiver.is_bot = False

    # Chat
    chat = MagicMock()
    chat.type = "private"
    chat.title = "Chat"
    message.chat = chat
    update.effective_chat = chat

    # Entities
    entity = MagicMock(spec=MessageEntity)
    entity.type = MessageEntity.TEXT_MENTION
    entity.user = receiver

    # Mock parse_entities return dict {entity: text}
    message.parse_entities.return_value = {entity: "Receiver"}

    message.reply_text = AsyncMock()
    context = MagicMock()

    await handle_gift_command(update, context)

    # Should ask what to gift to Receiver
    message.reply_text.assert_called_once()
    assert "Receiver" in message.reply_text.call_args[0][0]
    assert message.reply_text.call_args[1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_gift_command_mention_success():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    message.reply_to_message = None

    # Sender
    sender = MagicMock(spec=User)
    sender.id = 1
    sender.first_name = "Sender"
    sender.name = "Sender"
    sender.username = "sender"
    message.from_user = sender
    update.effective_user = sender

    # Chat
    chat = MagicMock()
    chat.type = "private"
    chat.title = "Chat"
    message.chat = chat
    update.effective_chat = chat

    # Entities
    entity = MagicMock(spec=MessageEntity)
    entity.type = MessageEntity.MENTION

    message.parse_entities.return_value = {entity: "@receiver"}

    # Mock DB user
    db_user = MagicMock(spec=User)
    db_user.id = 3
    db_user.first_name = "DB Receiver"
    db_user.is_bot = False

    message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("tg.handlers.commands.gift.services") as mock_services:
        mock_services.user_repo.get_by_username = AsyncMock(return_value=db_user)
        await handle_gift_command(update, context)

        mock_services.user_repo.get_by_username.assert_called_once_with("receiver")
        message.reply_text.assert_called_once()
        args, kwargs = message.reply_text.call_args
        assert "¿Qué detalle quieres tener con DB Receiver?" in args[0]
        assert "reply_markup" in kwargs


@pytest.mark.asyncio
async def test_handle_gift_command_mention_not_found():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message
    message.reply_to_message = None

    # Sender
    sender = MagicMock(spec=User)
    sender.id = 1
    sender.first_name = "Sender"
    sender.name = "Sender"
    sender.username = "sender"
    message.from_user = sender
    update.effective_user = sender

    # Chat
    chat = MagicMock()
    chat.type = "private"
    chat.title = "Chat"
    message.chat = chat
    update.effective_chat = chat

    # Entities
    entity = MagicMock(spec=MessageEntity)
    entity.type = MessageEntity.MENTION

    message.parse_entities.return_value = {entity: "@unknown"}

    message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("tg.handlers.commands.gift.services") as mock_services:
        mock_services.user_repo.get_by_username = AsyncMock(return_value=None)
        await handle_gift_command(update, context)

        mock_services.user_repo.get_by_username.assert_called_once_with("unknown")
        message.reply_text.assert_called_once_with(
            "⚠️ No conozco a @unknown. Dile que hable conmigo primero."
        )
