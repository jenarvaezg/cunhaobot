import asyncio
import pytest
from unittest.mock import MagicMock, patch
from tg.handlers.commands.start import handle_start


@pytest.mark.asyncio
async def test_handle_start():
    # Mock random phrase generation
    with (
        patch("models.phrase.Phrase.get_random_phrase") as mock_phrase,
        patch("models.phrase.LongPhrase.get_random_phrase") as mock_long_phrase,
        patch("tg.decorators.User") as mock_user_cls,
    ):
        mock_phrase.return_value = MagicMock(text="cuñao")
        mock_phrase.return_value.__str__.return_value = "cuñao"

        mock_long_phrase.return_value = MagicMock(text="frase larga")
        mock_long_phrase.return_value.__str__.return_value = "frase larga"

        mock_user_instance = MagicMock()
        mock_user_cls.update_or_create_from_update.return_value = mock_user_instance

        update = MagicMock()
        update.to_dict.return_value = {}
        context = MagicMock()

        # Mock reply_text as async
        f = asyncio.Future()
        f.set_result(None)
        update.effective_message.reply_text.return_value = f

        await handle_start(update, context)

        # Check that user was saved (via decorator)
        mock_user_instance.save.assert_called()

        # Check reply
        update.effective_message.reply_text.assert_called()
        args, _ = update.effective_message.reply_text.call_args
        msg = args[0]
        assert "cuñao" in msg
        assert "frase larga" in msg
