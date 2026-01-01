import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.help import handle_help


@pytest.mark.asyncio
async def test_handle_help():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    mock_phrase1 = MagicMock()
    mock_phrase1.text = "cuñao"
    mock_phrase2 = MagicMock()
    mock_phrase2.text = "frase"
    mock_phrase_long = MagicMock()
    mock_phrase_long.text = "frase larga"

    with (
        patch("tg.handlers.commands.help.phrase_service.get_random") as mock_get_random,
        patch("tg.decorators.user_service.update_or_create_user"),
    ):
        mock_get_random.side_effect = [mock_phrase1, mock_phrase2, mock_phrase_long]

        await handle_help(update, context)
        update.effective_message.reply_text.assert_called_once()
        args, _ = update.effective_message.reply_text.call_args
        msg = args[0]
        assert "cuñao" in msg
        assert "/cuñao" in msg
        assert "/perfil" in msg
        assert "@cunhaobot" in msg
