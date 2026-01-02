import pytest
from unittest.mock import MagicMock
from tg.utils.history import get_telegram_history
from pydantic_ai.messages import ModelRequest, ModelResponse


@pytest.mark.asyncio
async def test_get_telegram_history_no_reply_no_chat_data():
    message = MagicMock()
    message.reply_to_message = None
    message.message_id = 100

    context = MagicMock()
    context.chat_data = {}
    context.bot.id = 123

    history = await get_telegram_history(message, context)
    assert history == []


@pytest.mark.asyncio
async def test_get_telegram_history_with_chat_data():
    message = MagicMock()
    message.reply_to_message = None
    message.message_id = 100

    context = MagicMock()
    context.chat_data = {
        "history": [
            {
                "message_id": 1,
                "text": "Hello",
                "user_id": 456,
                "username": "user1",
                "date": 10,
            },
            {
                "message_id": 2,
                "text": "Hi",
                "user_id": 123,
                "username": "bot",
                "date": 20,
            },
        ]
    }
    context.bot.id = 123

    history = await get_telegram_history(message, context)

    assert len(history) == 2
    assert isinstance(history[0], ModelRequest)
    assert history[0].parts[0].content == "user1 dice: Hello"
    assert isinstance(history[1], ModelResponse)
    assert history[1].parts[0].content == "Hi"


@pytest.mark.asyncio
async def test_get_telegram_history_recursive_and_chat_data():
    bot_id = 123

    # Message in reply chain (older)
    msg1 = MagicMock()
    msg1.message_id = 1
    msg1.from_user.id = 456
    msg1.from_user.username = "user1"
    msg1.text = "Old Message"
    msg1.date = 10
    msg1.reply_to_message = None

    # Current message
    message = MagicMock()
    message.message_id = 3
    message.reply_to_message = msg1

    # Chat data has a newer message
    context = MagicMock()
    context.chat_data = {
        "history": [
            {
                "message_id": 2,
                "text": "Recent Message",
                "user_id": 456,
                "username": "user1",
                "date": 20,
            }
        ]
    }
    context.bot.id = bot_id

    history = await get_telegram_history(message, context)

    assert len(history) == 2
    # Ordered by date: msg1 (10), then msg2 (20)
    assert history[0].parts[0].content == "user1 dice: Old Message"
    assert history[1].parts[0].content == "user1 dice: Recent Message"


@pytest.mark.asyncio
async def test_get_telegram_history_deduplication():
    bot_id = 123

    # Same message in both reply chain and chat_data
    msg1 = MagicMock()
    msg1.message_id = 1
    msg1.from_user.id = 456
    msg1.from_user.username = "user1"
    msg1.text = "Hello"
    msg1.date = 10
    msg1.reply_to_message = None

    message = MagicMock()
    message.message_id = 2
    message.reply_to_message = msg1

    context = MagicMock()
    context.chat_data = {
        "history": [
            {
                "message_id": 1,
                "text": "Hello",
                "user_id": 456,
                "username": "user1",
                "date": 10,
            }
        ]
    }
    context.bot.id = bot_id

    history = await get_telegram_history(message, context)

    assert len(history) == 1
    assert history[0].parts[0].content == "user1 dice: Hello"
