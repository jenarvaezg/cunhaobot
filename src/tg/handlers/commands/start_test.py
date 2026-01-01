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
        patch("tg.decorators.user_service.update_or_create_user"),
    ):
        mock_get_random.return_value = mock_phrase1

        await handle_start(update, context)

    # Check reply
    update.effective_message.reply_text.assert_called_once()
    args, _ = update.effective_message.reply_text.call_args
    msg = args[0]
    assert "cuñao" in msg
    assert "Bienvenido" in msg
    assert "/perfil" in msg
    assert "@cunhaobot" in msg
