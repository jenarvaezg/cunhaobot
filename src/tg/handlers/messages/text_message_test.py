import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tg.handlers.messages.text_message import handle_message


@pytest.mark.asyncio
async def test_handle_message_trigger():
    update = MagicMock()
    update.effective_message.text = "Hola cuñao"
    update.effective_message.reply_text = AsyncMock()

    with (
        patch(
            "tg.handlers.messages.text_message.phrase_service.get_random"
        ) as mock_random,
        patch("tg.decorators.user_service.update_or_create_user"),
    ):
        mock_random.return_value.text = "random phrase"
        await handle_message(update, MagicMock())
        update.effective_message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_random_interaction():
    update = MagicMock()
    update.effective_message.text = "normal message"
    update.effective_message.reply_text = AsyncMock()

    with (
        patch(
            "tg.handlers.messages.text_message.phrase_service.get_random"
        ) as mock_random,
        patch("tg.decorators.user_service.update_or_create_user"),
        patch("random.random", return_value=0.01),  # Force interaction
    ):
        mock_random.return_value.text = "apelativo"
        await handle_message(update, MagicMock())
        update.effective_message.reply_text.assert_called_once()
        assert "apelativo" in update.effective_message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_message_no_interaction():
    update = MagicMock()
    update.effective_message.text = "normal message"
    update.effective_message.reply_text = AsyncMock()

    with (
        patch("tg.decorators.user_service.update_or_create_user"),
        patch("random.random", return_value=0.99),  # Force NO interaction
    ):
        await handle_message(update, MagicMock())
        update.effective_message.reply_text.assert_not_called()


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
    update.effective_message.chat.send_action = AsyncMock()
    update.effective_message.chat.type = "group"
    update.effective_message.reply_to_message = None

    context = MagicMock()
    context.bot.username = "TestBot"
    context.bot.id = 12345

    with (
        patch(
            "tg.handlers.messages.text_message.cunhao_agent.answer",
            new_callable=AsyncMock,
        ) as mock_answer,
        patch("tg.decorators.user_service.update_or_create_user"),
    ):
        mock_answer.return_value = "AI Response"
        await handle_message(update, context)

        mock_answer.assert_called_once()
        update.effective_message.reply_text.assert_called_once_with(
            "AI Response", do_quote=True
        )
