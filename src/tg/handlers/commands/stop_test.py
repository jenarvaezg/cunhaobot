import pytest
from unittest.mock import MagicMock, AsyncMock
from tg.handlers.commands.stop import handle_stop
from telegram import Chat


from test_factories import UserFactory, PhraseFactory


@pytest.mark.asyncio
async def test_handle_stop(mock_container):
    update = MagicMock()
    update.to_dict.return_value = {"update_id": 1}
    update.effective_user.id = 123
    update.effective_user.name = "testuser"
    update.effective_user.username = "testuser"
    update.effective_chat.id = 456
    update.effective_chat.type = Chat.PRIVATE
    update.effective_chat.title = "Chat"
    update.effective_chat.PRIVATE = Chat.PRIVATE
    update.effective_message.chat_id = 456
    update.effective_message.chat = update.effective_chat
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    mock_user = UserFactory.build(id=456, name="testuser")
    mock_phrase = PhraseFactory.build(text="cuñao")

    mock_container["user_repo"].load = AsyncMock(return_value=mock_user)
    mock_container["phrase_service"].get_random.return_value = mock_phrase

    await handle_stop(update, context)

    mock_container["user_service"].delete_user.assert_called_once_with(mock_user)
    update.effective_message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_stop_no_user():
    update = MagicMock()
    update.effective_user = None
    update.effective_chat.type = Chat.PRIVATE
    update.effective_message = None
    context = MagicMock()
    await handle_stop(update, context)
