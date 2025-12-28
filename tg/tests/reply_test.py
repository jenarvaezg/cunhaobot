import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.reply import handle_reply
from models.phrase import Phrase, LongPhrase


class TestReplyHandlers:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Mock random phrase generation
        self.patcher_phrase = patch(
            "models.phrase.Phrase.get_random_phrase", return_value="cuñao"
        )
        self.mock_phrase = self.patcher_phrase.start()
        yield
        self.patcher_phrase.stop()

    @pytest.mark.asyncio
    async def test_handle_reply_not_me(self):
        update = MagicMock()
        update.effective_message.reply_to_message.from_user.username = "not_me"
        update.effective_message.reply_to_message.text = "some text"

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        context = MagicMock()
        context.bot = bot

        await handle_reply(update, context)
        # Should return early
        update.effective_message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_reply_to_phrase_proposal(self):
        update = MagicMock()
        update.effective_message.text = "new phrase"
        update.effective_message.reply_to_message.from_user.username = "me"
        update.effective_message.reply_to_message.text = (
            f"¿Qué {Phrase.name} quieres proponer?"
        )

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        context = MagicMock()
        context.bot = bot

        with patch(
            "tg.handlers.reply.handle_submit", new_callable=AsyncMock
        ) as mock_submit:
            await handle_reply(update, context)
            mock_submit.assert_called_once()
            assert update.effective_message.text == "/proponer new phrase"

    @pytest.mark.asyncio
    async def test_handle_reply_to_long_phrase_proposal(self):
        update = MagicMock()
        update.effective_message.text = "new long phrase"
        update.effective_message.reply_to_message.from_user.username = "me"
        update.effective_message.reply_to_message.text = (
            f"¿Qué {LongPhrase.name} quieres proponer?"
        )

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        context = MagicMock()
        context.bot = bot

        with patch(
            "tg.handlers.reply.handle_submit_phrase", new_callable=AsyncMock
        ) as mock_submit:
            await handle_reply(update, context)
            mock_submit.assert_called_once()
            assert update.effective_message.text == "/proponerfrase new long phrase"
