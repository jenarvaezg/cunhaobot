import pytest
from unittest.mock import MagicMock, AsyncMock
from tg.handlers.commands.help import handle_help


from test_factories import PhraseFactory


@pytest.mark.asyncio
async def test_handle_help(mock_container):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    mock_phrase1 = PhraseFactory.build(text="cuñao")

    mock_container["phrase_service"].get_random.return_value = mock_phrase1
    mock_container["usage_service"].log_usage.return_value = []

    await handle_help(update, context)

    # Check for at least one call (due to badges)
    assert update.effective_message.reply_text.call_count >= 1

    # Verify content of help message
    call_args_list = update.effective_message.reply_text.call_args_list
    help_call = None
    for call_obj in call_args_list:
        args, _ = call_obj
        if "Cuñao Vision" in args[0]:
            help_call = call_obj
            break

    assert help_call is not None
    args, _ = help_call
    msg = args[0]
    assert "/poster" in msg
    assert "/perfil" in msg
    assert "@cunhaobot" in msg
