import unittest
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from tg.handlers.start import handle_start
from tg.handlers.text_message import handle_message
from models.phrase import Phrase, LongPhrase

class TestHandlers:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Mock random phrase generation
        self.patcher_phrase = patch('models.phrase.Phrase.get_random_phrase')
        self.mock_get_random_phrase = self.patcher_phrase.start()
        self.mock_get_random_phrase.return_value = MagicMock(text="cuñao")
        self.mock_get_random_phrase.return_value.__str__.return_value = "cuñao"

        self.patcher_long_phrase = patch('models.phrase.LongPhrase.get_random_phrase')
        self.mock_get_long_random_phrase = self.patcher_long_phrase.start()
        self.mock_get_long_random_phrase.return_value = MagicMock(text="frase larga")
        self.mock_get_long_random_phrase.return_value.__str__.return_value = "frase larga"
        
        # Mock User model interaction to avoid datastore calls in decorators
        # We must patch where it is used (tg.decorators) because it was already imported
        self.patcher_user = patch('tg.decorators.User')
        self.mock_user_cls = self.patcher_user.start()
        self.mock_user_instance = MagicMock()
        self.mock_user_cls.update_or_create_from_update.return_value = self.mock_user_instance
        
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
