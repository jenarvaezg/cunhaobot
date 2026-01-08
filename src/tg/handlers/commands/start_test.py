import pytest
from unittest.mock import MagicMock, AsyncMock
from tg.handlers.commands.start import handle_start


from test_factories import PhraseFactory


@pytest.mark.asyncio
async def test_handle_start(mock_container):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.reply_text = AsyncMock()
    update.to_dict.return_value = {}
    context = MagicMock()

    mock_phrase1 = PhraseFactory.build(text="cuñao")

    mock_container["phrase_service"].get_random.return_value = mock_phrase1
    mock_container["usage_service"].log_usage.return_value = []

    await handle_start(update, context)

    # Check reply (at least once due to badges)
    assert update.effective_message.reply_text.call_count >= 1

    # Verify content
    call_args_list = update.effective_message.reply_text.call_args_list
    start_call = None
    for call_obj in call_args_list:
        args, _ = call_obj
        if "Bienvenido" in args[0]:
            start_call = call_obj
            break

    assert start_call is not None
    args, _ = start_call
    msg = args[0]
    assert "cuñao" in msg
    assert "/perfil" in msg
    assert "@cunhaobot" in msg
