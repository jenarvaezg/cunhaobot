import pytest
from unittest.mock import MagicMock, AsyncMock
from tg.handlers.commands.about import handle_about
from models.phrase import Phrase


from unittest.mock import call


@pytest.mark.asyncio
async def test_handle_about(mock_container):
    update = MagicMock()
    message = MagicMock()
    user = MagicMock()

    user.id = 12345
    user.name = "Test User"
    user.username = "test_user"

    message.reply_text = AsyncMock()
    message.chat.title = "Test Chat"
    message.chat.PRIVATE = "private"
    message.chat.type = "group"
    message.chat_id = 1

    update.effective_message = message
    update.effective_user = user

    context = MagicMock()

    mock_phrase = Phrase(text="cuñao")

    mock_container["usage_service"].log_usage.return_value = []
    mock_container["phrase_service"].get_random.return_value = mock_phrase

    await handle_about(update, context)

    # Check that reply_text was called at least once with the about message
    assert message.reply_text.call_count >= 1
    # Check the specific call
    expected_text = (
        "Este bot ha sido creado por un cuñao muy aburrido.\n"
        "Puedes ver el código fuente en GitHub: https://github.com/josesarmiento/cunhaobot"
    )
    assert call(expected_text, do_quote=True) in message.reply_text.call_args_list
