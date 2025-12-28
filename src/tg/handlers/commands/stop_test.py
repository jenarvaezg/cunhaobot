import asyncio
import pytest
from unittest.mock import MagicMock, patch
from tg.handlers.commands.stop import handle_stop
from models.user import User
from telegram import Chat


@pytest.mark.asyncio
async def test_handle_stop():
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
