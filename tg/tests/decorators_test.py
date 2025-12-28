import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.decorators import only_admins, log_update
from telegram import Chat


async def dummy_func(update, context):
    return "ok"


class TestDecorators:
    @pytest.mark.asyncio
    async def test_only_admins_private(self):
        decorated = only_admins(dummy_func)
        update = MagicMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE

        res = await decorated(update, MagicMock())
        assert res == "ok"

    @pytest.mark.asyncio
    async def test_only_admins_not_admin(self):
        decorated = only_admins(dummy_func)
        update = MagicMock()
        update.effective_chat.type = "group"
        update.effective_chat.get_administrators = AsyncMock(
            return_value=[MagicMock(user=MagicMock(id=1))]
        )
        update.effective_user.id = 2
        update.effective_message.reply_text = AsyncMock()

        with patch("models.phrase.Phrase.get_random_phrase", return_value="cuñao"):
            await decorated(update, MagicMock())
            update.effective_message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_only_admins_no_chat(self):
        decorated = only_admins(dummy_func)
        update = MagicMock()
        update.effective_chat = None
        assert await decorated(update, MagicMock()) is None

    @pytest.mark.asyncio
    async def test_only_admins_no_user(self):
        decorated = only_admins(dummy_func)
        update = MagicMock()
        update.effective_chat.type = "group"
        update.effective_chat.get_administrators = AsyncMock(return_value=[])
        update.effective_user = None
        update.effective_message = MagicMock()
        update.effective_message.reply_text = AsyncMock()
        with patch("models.phrase.Phrase.get_random_phrase", return_value="cuñao"):
            assert await decorated(update, MagicMock()) is None
            update.effective_message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_only_admins_success(self):
        decorated = only_admins(dummy_func)
        update = MagicMock()
        update.effective_chat.type = "group"
        update.effective_chat.get_administrators = AsyncMock(
            return_value=[MagicMock(user=MagicMock(id=1))]
        )
        update.effective_user.id = 1
        assert await decorated(update, MagicMock()) == "ok"

    @pytest.mark.asyncio
    async def test_log_update_no_chat(self):
        decorated = log_update(dummy_func)
        update = MagicMock()
        update.effective_chat = None
        assert await decorated(update, MagicMock()) == "ok"

    @pytest.mark.asyncio
    async def test_log_update_no_user(self):
        decorated = log_update(dummy_func)
        update = MagicMock()
        update.to_dict.return_value = {}
        with patch("models.user.User.update_or_create_from_update", return_value=None):
            assert await decorated(update, MagicMock()) == "ok"

    @pytest.mark.asyncio
    async def test_log_update_success(self):
        decorated = log_update(dummy_func)
        update = MagicMock()
        update.to_dict.return_value = {"a": 1}

        with patch("models.user.User.update_or_create_from_update") as mock_user_get:
            mock_user = MagicMock()
            mock_user_get.return_value = mock_user
            res = await decorated(update, MagicMock())
            assert res == "ok"
            mock_user.save.assert_called_once()
