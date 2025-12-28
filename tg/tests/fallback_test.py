import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.fallback import (
    handle_fallback_message,
    _on_kick,
    _on_join,
    _on_migrate,
)


class TestFallbackHandlers:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.patcher_phrase = patch(
            "models.phrase.Phrase.get_random_phrase",
            return_value=MagicMock(text="cuñao"),
        )
        self.mock_phrase = self.patcher_phrase.start()
        # Mock ScheduledTask.get_tasks globally for fallback tests to avoid KeyErrors
        self.patcher_tasks = patch(
            "models.schedule.ScheduledTask.get_tasks", return_value=[]
        )
        self.patcher_tasks.start()
        yield
        self.patcher_phrase.stop()
        self.patcher_tasks.stop()

    @pytest.mark.asyncio
    async def test_handle_fallback_kick_self(self):
        update = MagicMock()
        update.effective_message.left_chat_member.username = "me"
        update.effective_message.chat_id = 456

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        context = MagicMock()
        context.bot = bot

        with patch("tg.handlers.fallback._on_kick") as mock_kick:
            await handle_fallback_message(update, context)
            mock_kick.assert_called_once_with(456)

    @pytest.mark.asyncio
    async def test_handle_fallback_kick_other(self):
        update = MagicMock()
        update.effective_message.left_chat_member.username = "other"
        update.effective_message.left_chat_member.name = "other_name"
        update.effective_message.chat_id = 456

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        bot.send_message = AsyncMock()
        context = MagicMock()
        context.bot = bot

        await handle_fallback_message(update, context)
        bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_fallback_join_self(self):
        update = MagicMock()
        update.effective_message.left_chat_member = None
        new_user = MagicMock()
        new_user.username = "me"
        update.effective_message.new_chat_members = [new_user]
        update.effective_message.chat_id = 456

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        bot.send_message = AsyncMock()
        context = MagicMock()
        context.bot = bot

        await handle_fallback_message(update, context)
        bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_fallback_join_other(self):
        update = MagicMock()
        update.effective_message.left_chat_member = None
        new_user = MagicMock()
        new_user.username = "other"
        new_user.name = "other_name"
        update.effective_message.new_chat_members = [new_user]
        update.effective_message.chat_id = 456

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        bot.send_message = AsyncMock()
        context = MagicMock()
        context.bot = bot

        await handle_fallback_message(update, context)
        bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_join(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        await _on_join(bot, 123)
        bot.send_message.assert_called_once()

    def test_on_kick(self):
        with (
            patch("models.user.User.load") as mock_load,
            patch("models.schedule.ScheduledTask.get_tasks") as mock_tasks,
        ):
            mock_user = MagicMock()
            mock_load.return_value = mock_user

            mock_task = MagicMock()
            mock_tasks.return_value = [mock_task]

            _on_kick(123)
            mock_user.delete.assert_called_once()
            mock_task.delete.assert_called_once()

    def test_on_migrate(self):
        with (
            patch("models.user.User.load") as mock_load,
            patch("models.schedule.ScheduledTask.get_tasks") as mock_tasks,
        ):
            mock_user = MagicMock()
            mock_load.return_value = mock_user

            mock_task = MagicMock()
            mock_tasks.return_value = [mock_task]

            _on_migrate(123, 456)
            mock_user.save.assert_called_once()
            assert mock_user.chat_id == 456
            mock_task.save.assert_called_once()
            assert mock_task.chat_id == 456

    def test_on_migrate_full(self):
        # Hit fallback.py 44-46
        with (
            patch("models.user.User.load") as mock_load,
            patch("models.schedule.ScheduledTask.get_tasks", return_value=[]),
        ):
            mock_user = MagicMock()
            mock_load.return_value = mock_user
            _on_migrate(123, 456)
            mock_user.delete.assert_called_with(hard=True)
            assert mock_user.chat_id == 456
            mock_user.save.assert_called()
