import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import ReactionTypeEmoji
from tg.handlers.messages.text_message import handle_message


@pytest.mark.asyncio
async def test_handle_message_empty():
    update = MagicMock()
    update.effective_message = None
    assert await handle_message(update, MagicMock()) is None


@pytest.mark.asyncio
async def test_handle_message_mention_trigger(mock_container):
    update = MagicMock()
    user = MagicMock()
    user.id = 123
    user.name = "Test User"
    user.username = "testuser"

    chat = MagicMock()
    chat.id = 123
    chat.type = "group"
    chat.title = "Chat"

    update.effective_user = user
    update.effective_chat = chat
    update.effective_message.text = "Hola @TestBot"
    update.effective_message.reply_text = AsyncMock()
    update.effective_message.set_reaction = AsyncMock()
    update.effective_message.chat.send_action = AsyncMock()
    update.effective_message.chat.type = "group"
    update.effective_message.reply_to_message = None
    update.effective_message.from_user.id = 123
    update.effective_message.from_user.username = "testuser"

    context = MagicMock()
    context.bot.username = "TestBot"
    context.bot.id = 12345

    mock_chat = MagicMock()
    mock_chat.is_premium = True
    mock_container["chat_repo"].load = AsyncMock(return_value=mock_chat)
    mock_container["cunhao_agent"].answer.return_value = "AI Response"
    mock_container["usage_service"].log_usage.return_value = []
    mock_container["ai_service"].analyze_sentiment_and_react.return_value = "🍺"

    await handle_message(update, context)

    mock_container["cunhao_agent"].answer.assert_called_once()
    update.effective_message.reply_text.assert_called_once_with(
        "AI Response", do_quote=True
    )
    mock_container["ai_service"].analyze_sentiment_and_react.assert_called_once_with(
        "Hola @TestBot"
    )
    update.effective_message.set_reaction.assert_called_once_with(
        reaction=ReactionTypeEmoji("🍺")
    )


@pytest.mark.asyncio
async def test_handle_message_no_trigger_only_reaction(mock_container):
    update = MagicMock()
    user = MagicMock()
    user.id = 123
    user.name = "Test User"
    user.username = "testuser"

    chat = MagicMock()
    chat.id = 123
    chat.type = "group"
    chat.title = "Chat"

    update.effective_user = user
    update.effective_chat = chat
    update.effective_message.text = "Solo un mensaje en el grupo"
    update.effective_message.reply_text = AsyncMock()
    update.effective_message.set_reaction = AsyncMock()
    update.effective_message.chat.send_action = AsyncMock()
    update.effective_message.chat.type = "group"
    update.effective_message.reply_to_message = None
    update.effective_message.from_user.id = 123

    context = MagicMock()
    context.bot.username = "TestBot"
    context.bot.id = 12345

    mock_chat = MagicMock()
    mock_chat.is_premium = True
    mock_container["chat_repo"].load = AsyncMock(return_value=mock_chat)
    mock_container["ai_service"].analyze_sentiment_and_react.return_value = "🇪🇸"

    await handle_message(update, context)

    # Should NOT answer
    mock_container["cunhao_agent"].answer.assert_not_called()
    update.effective_message.reply_text.assert_not_called()

    # Should react
    mock_container["ai_service"].analyze_sentiment_and_react.assert_called_once_with(
        "Solo un mensaje en el grupo"
    )
    update.effective_message.set_reaction.assert_called_once_with(
        reaction=ReactionTypeEmoji("🇪🇸")
    )
