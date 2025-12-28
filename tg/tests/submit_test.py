import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.submit import handle_submit, handle_submit_phrase, submit_handling
from models.proposal import Proposal
from models.phrase import Phrase
from telegram import ForceReply


class TestSubmitHandlers:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Mock Phrase.get_random_phrase
        self.patcher_phrase = patch("models.phrase.Phrase.get_random_phrase")
        self.mock_phrase = self.patcher_phrase.start()
        self.mock_phrase.return_value = "cuñao"

        yield
        self.patcher_phrase.stop()

    @pytest.mark.asyncio
    async def test_handle_submit_too_long(self):
        update = MagicMock()
        update.effective_message.text = "/proponer one two three four five six"
        update.effective_message.reply_text = AsyncMock()
        context = MagicMock()

        await handle_submit(update, context)
        update.effective_message.reply_text.assert_called()
        args, _ = update.effective_message.reply_text.call_args
        assert "¿Estás seguro de que esto es una frase corta" in args[0]

    @pytest.mark.asyncio
    async def test_submit_handling_no_text(self):
        update = MagicMock()
        update.effective_user.name = "test_user"
        update.effective_message.text = "/proponer"
        update.effective_message.reply_to_message = None
        update.effective_message.reply_text = AsyncMock()

        # Proposal.from_update will return a proposal with empty text
        await submit_handling(MagicMock(), update, Proposal, Phrase)

        update.effective_message.reply_text.assert_called()
        _, kwargs = update.effective_message.reply_text.call_args
        assert isinstance(kwargs["reply_markup"], ForceReply)

    @pytest.mark.asyncio
    async def test_submit_handling_duplicate(self):
        update = MagicMock()
        update.effective_user.name = "test_user"
        update.effective_message.text = "/proponer existing"
        update.effective_message.reply_text = AsyncMock()

        with patch.object(Phrase, "get_most_similar", return_value=("existing", 100)):
            await submit_handling(MagicMock(), update, Proposal, Phrase)

            update.effective_message.reply_text.assert_called()
            args, _ = update.effective_message.reply_text.call_args
            assert "Esa ya la tengo" in args[0]

    @pytest.mark.asyncio
    async def test_submit_handling_similar(self):
        update = MagicMock()
        update.effective_user.name = "test_user"
        update.effective_message.text = "/proponer similar"
        update.effective_message.reply_text = AsyncMock()

        with patch.object(Phrase, "get_most_similar", return_value=("existing", 95)):
            await submit_handling(MagicMock(), update, Proposal, Phrase)

            update.effective_message.reply_text.assert_called()
            args, _ = update.effective_message.reply_text.call_args
            assert "Se parece demasiado" in args[0]

    @pytest.mark.asyncio
    async def test_submit_handling_success(self):
        update = MagicMock()
        update.effective_user.name = "test_user"
        update.effective_user.id = 123
        update.effective_message.text = "/proponer new phrase"
        update.effective_message.chat.id = 456
        update.effective_message.message_id = 789
        update.effective_message.reply_text = AsyncMock()

        bot = MagicMock()
        bot.send_message = AsyncMock()

        mock_phrase = MagicMock(spec=Phrase)
        mock_phrase.name = "phrase"
        mock_phrase.__str__.return_value = "nothing"

        with (
            patch.object(Phrase, "get_most_similar", return_value=(mock_phrase, 0)),
            patch("models.proposal.Proposal.save") as mock_save,
        ):
            await submit_handling(bot, update, Proposal, Phrase)

            mock_save.assert_called_once()
            bot.send_message.assert_called_once()
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_submit_success(self):
        update = MagicMock()
        update.effective_message.text = "/proponer short"
        update.effective_user.name = "user"

        with patch(
            "tg.handlers.submit.submit_handling", new_callable=AsyncMock
        ) as mock_sub:
            await handle_submit(update, MagicMock())
            mock_sub.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_submit_phrase(self):
        update = MagicMock()
        update.effective_message.text = "/proponerfrase long one"
        update.effective_message.reply_text = AsyncMock()
        context = MagicMock()

        with patch(
            "tg.handlers.submit.submit_handling", new_callable=AsyncMock
        ) as mock_handling:
            await handle_submit_phrase(update, context)
            mock_handling.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_submit_no_text(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message.text = None
        await handle_submit(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_submit_no_message_return(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message = None
        await handle_submit(update, MagicMock())

    @pytest.mark.asyncio
    async def test_submit_handling_value_error(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_user = None
        with pytest.raises(ValueError, match="Update has no effective user or message"):
            await submit_handling(MagicMock(), update, Proposal, Phrase)

    @pytest.mark.asyncio
    async def test_handle_submit_phrase_no_message_return_line93_fixed(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message = None

        func = handle_submit_phrase
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__
        await func(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_submit_phrase_success_line93(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message.text = "/proponerfrase phrase"
        update.effective_user.name = "user"

        func = handle_submit_phrase
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__

        with patch(
            "tg.handlers.submit.submit_handling", new_callable=AsyncMock
        ) as mock_sub:
            await func(update, MagicMock())
            mock_sub.assert_called_once()
