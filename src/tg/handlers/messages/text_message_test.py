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
