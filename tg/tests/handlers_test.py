import asyncio
from unittest.mock import MagicMock, patch

import pytest

from tg.handlers.start import handle_start
from tg.handlers.text_message import handle_message


class TestHandlers:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Mock random phrase generation
        self.patcher_phrase = patch("models.phrase.Phrase.get_random_phrase")
        self.mock_get_random_phrase = self.patcher_phrase.start()
        self.mock_get_random_phrase.return_value = MagicMock(text="cuñao")
        self.mock_get_random_phrase.return_value.__str__.return_value = "cuñao"

        self.patcher_long_phrase = patch("models.phrase.LongPhrase.get_random_phrase")
        self.mock_get_long_random_phrase = self.patcher_long_phrase.start()
        self.mock_get_long_random_phrase.return_value = MagicMock(text="frase larga")
        self.mock_get_long_random_phrase.return_value.__str__.return_value = (
            "frase larga"
        )

        # Mock User model interaction to avoid datastore calls in decorators
        # We must patch where it is used (tg.decorators) because it was already imported
        self.patcher_user = patch("tg.decorators.User")
        self.mock_user_cls = self.patcher_user.start()
        self.mock_user_instance = MagicMock()
        self.mock_user_cls.update_or_create_from_update.return_value = (
            self.mock_user_instance
        )

        yield

        self.patcher_phrase.stop()
        self.patcher_long_phrase.stop()
        self.patcher_user.stop()

    @pytest.mark.asyncio
    async def test_handle_start(self):
        update = MagicMock()
        update.to_dict.return_value = {}
        context = MagicMock()

        # Mock reply_text as async
        f = asyncio.Future()
        f.set_result(None)
        update.effective_message.reply_text.return_value = f

        await handle_start(update, context)

        # Check that user was saved (via decorator)
        self.mock_user_instance.save.assert_called()

        # Check reply
        update.effective_message.reply_text.assert_called()
        args, _ = update.effective_message.reply_text.call_args
        msg = args[0]
        assert "cuñao" in msg
        assert "frase larga" in msg

    @pytest.mark.asyncio
    async def test_handle_message_trigger(self):
        update = MagicMock()
        update.to_dict.return_value = {}
        context = MagicMock()
        update.effective_message.text = "hola cunhaobot"

        f = asyncio.Future()
        f.set_result(None)
        update.effective_message.reply_text.return_value = f

        await handle_message(update, context)

        # Check reply
        update.effective_message.reply_text.assert_called()
        args, _ = update.effective_message.reply_text.call_args
        msg = args[0]
        assert "Aquí me tienes" in msg

    @pytest.mark.asyncio
    async def test_handle_message_no_trigger(self):
        update = MagicMock()
        update.to_dict.return_value = {}
        context = MagicMock()
        update.effective_message.text = "hola gente"

        await handle_message(update, context)

        # Should not reply
        update.effective_message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_message_no_text(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message.text = None
        await handle_message(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_message_continue_coverage(self):
        # From missing_lines_test.py
        from models.phrase import Phrase
        from tg.handlers.text_message import reply_cunhao

        Phrase.phrases_cache = [Phrase(text="p1")]
        update = MagicMock()
        update.effective_message.text = "cuñao cuñao"
        # Mock reply_text as AsyncMock
        from unittest.mock import AsyncMock

        update.effective_message.reply_text = AsyncMock()

        # Patch MESSAGE_TRIGGERS to have two entries pointing to the same function
        mock_triggers = {
            ("cuñao",): reply_cunhao,
            ("cunhao",): reply_cunhao,
        }
        with patch("tg.handlers.text_message.MESSAGE_TRIGGERS", mock_triggers):
            await handle_message(update, MagicMock())
            # Line 32 in text_message.py should now be hit

    @pytest.mark.asyncio
    async def test_handle_stop(self):
        # From misc_handlers_test.py
        from tg.handlers.stop import handle_stop
        from models.user import User
        from telegram import Chat

        update = MagicMock()
        update.to_dict.return_value = {"update_id": 1}
        update.effective_user.id = 123
        update.effective_chat.id = 456
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        update.effective_message.reply_text = MagicMock(return_value=asyncio.Future())
        update.effective_message.reply_text.return_value.set_result(None)
        context = MagicMock()

        mock_user = MagicMock(spec=User)
        with (
            patch("models.user.User.load", return_value=mock_user),
            patch("models.schedule.ScheduledTask.get_tasks", return_value=[]),
        ):
            await handle_stop(update, context)
            mock_user.delete.assert_called_once()
            update.effective_message.reply_text.assert_called()
