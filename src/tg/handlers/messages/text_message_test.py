import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tg.handlers.messages.text_message import handle_message


@pytest.mark.asyncio
async def test_handle_message_empty():
    update = MagicMock()
    update.effective_message = None
    assert await handle_message(update, MagicMock()) is None


@pytest.mark.asyncio
async def test_handle_message_mention_trigger():
    update = MagicMock()
    update.effective_message.text = "Hola @TestBot"
    update.effective_message.reply_text = AsyncMock()
    update.effective_message.set_reaction = AsyncMock()
    update.effective_message.chat.send_action = AsyncMock()
    update.effective_message.chat.type = "group"
    update.effective_message.reply_to_message = None
    update.effective_message.from_user.id = 123

    context = MagicMock()
    context.bot.username = "TestBot"
    context.bot.id = 12345

    with (
        patch(
            "tg.handlers.messages.text_message.cunhao_agent.answer",
            new_callable=AsyncMock,
        ) as mock_answer,
        patch(
            "tg.handlers.messages.text_message.usage_service.log_usage",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "tg.handlers.messages.text_message.ai_service.analyze_sentiment_and_react",
            new_callable=AsyncMock,
        ) as mock_react,
        patch("tg.decorators.user_service.update_or_create_user"),
    ):
        mock_answer.return_value = "AI Response"
        mock_react.return_value = "🍺"

        await handle_message(update, context)

        mock_answer.assert_called_once()
        update.effective_message.reply_text.assert_called_once_with(
            "AI Response", do_quote=True
        )
        mock_react.assert_called_once_with("Hola @TestBot")
        update.effective_message.set_reaction.assert_called_once_with(reaction="🍺")


@pytest.mark.asyncio
async def test_handle_message_no_trigger_only_reaction():
    update = MagicMock()
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

    with (
        patch(
            "tg.handlers.messages.text_message.cunhao_agent.answer",
            new_callable=AsyncMock,
        ) as mock_answer,
        patch(
            "tg.handlers.messages.text_message.usage_service.log_usage",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "tg.handlers.messages.text_message.ai_service.analyze_sentiment_and_react",
            new_callable=AsyncMock,
        ) as mock_react,
        patch("tg.decorators.user_service.update_or_create_user"),
    ):
        mock_react.return_value = "🇪🇸"

        await handle_message(update, context)

        # Should NOT answer
        mock_answer.assert_not_called()
        update.effective_message.reply_text.assert_not_called()

        # Should react
        mock_react.assert_called_once_with("Solo un mensaje en el grupo")
        update.effective_message.set_reaction.assert_called_once_with(reaction="🇪🇸")
