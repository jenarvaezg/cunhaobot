import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import ReactionTypeEmoji
from tg.handlers.messages.text_message import handle_message
from services.chat_interaction_service import AIReply, ReactionDecision


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

    cis = mock_container["chat_interaction_service"]
    cis.answer.return_value = AIReply(text="AI Response", new_badges=[])
    cis.decide_reaction.return_value = ReactionDecision(emoji="🍺")
    cis.record_reaction_received.return_value = []

    await handle_message(update, context)

    # Mention strips the bot handle before asking the shared interaction module.
    cis.answer.assert_awaited_once_with(user_id=123, platform="telegram", text="Hola")
    update.effective_message.reply_text.assert_called_once_with(
        "AI Response", do_quote=True
    )
    cis.decide_reaction.assert_awaited_once_with("Hola @TestBot")
    update.effective_message.set_reaction.assert_called_once_with(
        reaction=ReactionTypeEmoji("🍺")
    )
    cis.record_reaction_received.assert_awaited_once()


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

    cis = mock_container["chat_interaction_service"]
    cis.decide_reaction.return_value = ReactionDecision(emoji="🇪🇸")
    cis.record_reaction_received.return_value = []

    await handle_message(update, context)

    # No direct interaction: no AI answer, but a smart reaction still applies.
    cis.answer.assert_not_called()
    update.effective_message.reply_text.assert_not_called()
    cis.decide_reaction.assert_awaited_once_with("Solo un mensaje en el grupo")
    update.effective_message.set_reaction.assert_called_once_with(
        reaction=ReactionTypeEmoji("🇪🇸")
    )
