import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.start import handle_start


@pytest.mark.asyncio
async def test_handle_start():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.to_dict.return_value = {}
    context = MagicMock()

    mock_phrase1 = MagicMock()
    mock_phrase1.text = "cuñao"
    mock_phrase2 = MagicMock()
    mock_phrase2.text = "amigo"
    mock_long_phrase = MagicMock()
    mock_long_phrase.text = "frase larga"

    with (
        patch(
            "tg.handlers.commands.start.phrase_service.get_random"
        ) as mock_get_random,
        patch("tg.decorators.user_service.update_or_create_user") as mock_user_update,
    ):
        mock_get_random.side_effect = [mock_phrase1, mock_phrase2, mock_long_phrase]

        await handle_start(update, context)

        # Check that user was updated (via decorator)
        mock_user_update.assert_called_once_with(update)

        # Check reply
        update.effective_message.reply_text.assert_called_once()
        args, _ = update.effective_message.reply_text.call_args
        msg = args[0]
        assert "cuñao" in msg
        assert "amigo" in msg
        assert "frase larga" in msg
