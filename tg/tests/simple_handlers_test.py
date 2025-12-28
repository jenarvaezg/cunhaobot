import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.about import handle_about
from tg.handlers.cancel import handle_cancel
from tg.handlers.help import handle_help
from tg.handlers.error import error_handler
from tg.handlers.start import handle_start
from tg.handlers.stop import handle_stop


class TestSimpleHandlers:
    @pytest.mark.asyncio
    async def test_handle_start(self):
        update = MagicMock()
        update.effective_message.reply_text = AsyncMock()
        with (
            patch("models.phrase.Phrase.get_random_phrase", return_value="cuñao"),
            patch("models.phrase.LongPhrase.get_random_phrase", return_value="frase"),
        ):
            await handle_start(update, MagicMock())
            update.effective_message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_stop(self):
        update = MagicMock()
        update.effective_user.id = 1
        update.effective_chat.id = 123
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = "private"
        update.effective_chat.PRIVATE = "private"

        with (
            patch("models.user.User.load", return_value=MagicMock()),
            patch(
                "models.schedule.ScheduledTask.get_tasks", return_value=[MagicMock()]
            ),
        ):
            await handle_stop(update, MagicMock())
            # check for chapas plural in message
            args, _ = update.effective_message.reply_text.call_args
            assert "chapas" in args[0]

    @pytest.mark.asyncio
    async def test_handle_about(self):
        update = MagicMock()
        update.effective_message.reply_text = AsyncMock()
        context = MagicMock()
        await handle_about(update, context)
        update.effective_message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cancel(self):
        update = MagicMock()
        update.effective_message.reply_text = AsyncMock()
        context = MagicMock()
        with patch("models.phrase.Phrase.get_random_phrase", return_value="cuñao"):
            await handle_cancel(update, context)
            update.effective_message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_help(self):
        update = MagicMock()
        update.effective_message.reply_text = AsyncMock()
        context = MagicMock()
        with (
            patch("models.phrase.Phrase.get_random_phrase", return_value="cuñao"),
            patch("models.phrase.LongPhrase.get_random_phrase", return_value="frase"),
        ):
            await handle_help(update, context)
            update.effective_message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handler(self):
        context = MagicMock()
        context.error = ValueError("test error")
        with pytest.raises(ValueError):
            await error_handler(MagicMock(), context)
