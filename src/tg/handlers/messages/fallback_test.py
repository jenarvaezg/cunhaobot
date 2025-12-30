import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tg.handlers.messages.fallback import handle_fallback_message, _on_kick, _on_migrate
from models.user import User


class TestFallbackHandlers:
    @pytest.mark.asyncio
    async def test_handle_fallback_join_other(self):
        update = MagicMock()
        update.effective_message.left_chat_member = None
        new_user = MagicMock()
        new_user.username = "other"
        new_user.name = "@other"
        update.effective_message.new_chat_members = [new_user]

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        bot.send_message = AsyncMock()
        context = MagicMock()
        context.bot = bot

        mock_phrase = MagicMock()
        mock_phrase.text = "cuñao"

        with (
            patch(
                "tg.handlers.messages.fallback.phrase_service.get_random",
                return_value=mock_phrase,
            ),
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            await handle_fallback_message(update, context)
            bot.send_message.assert_called_once()
            args, _ = bot.send_message.call_args
            assert "@other" in args[1]

    @pytest.mark.asyncio
    async def test_handle_fallback_join_me(self):
        update = MagicMock()
        me_user = MagicMock()
        me_user.username = "me"
        update.effective_message.new_chat_members = [me_user]
        update.effective_message.left_chat_member = None

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        bot.send_message = AsyncMock()
        context = MagicMock()
        context.bot = bot

        mock_phrase = MagicMock()
        mock_phrase.text = "cuñao"

        with (
            patch(
                "tg.handlers.messages.fallback.phrase_service.get_random",
                return_value=mock_phrase,
            ),
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            await handle_fallback_message(update, context)
            bot.send_message.assert_called_once()
            assert (
                "Ayuda" in bot.send_message.call_args[0][1]
                or "/help" in bot.send_message.call_args[0][1]
            )

    @pytest.mark.asyncio
    async def test_handle_fallback_kick_me(self):
        update = MagicMock()
        me_user = MagicMock()
        me_user.username = "me"
        update.effective_message.left_chat_member = me_user
        update.effective_message.new_chat_members = []

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        context = MagicMock()
        context.bot = bot

        with (
            patch("tg.handlers.messages.fallback._on_kick") as mock_kick,
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            await handle_fallback_message(update, context)
            mock_kick.assert_called_once_with(update.effective_message.chat_id)

    @pytest.mark.asyncio
    async def test_handle_fallback_kick_other(self):
        update = MagicMock()
        other_user = MagicMock()
        other_user.username = "other"
        other_user.name = "Paco"
        update.effective_message.left_chat_member = other_user
        update.effective_message.new_chat_members = []

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        bot.send_message = AsyncMock()
        context = MagicMock()
        context.bot = bot

        mock_phrase = MagicMock()
        mock_phrase.text = "maestro"

        with (
            patch(
                "tg.handlers.messages.fallback.phrase_service.get_random",
                return_value=mock_phrase,
            ),
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            await handle_fallback_message(update, context)
            bot.send_message.assert_called_once()
            assert "Paco" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_handle_fallback_migrate_to(self):
        update = MagicMock()
        update.effective_message.migrate_to_chat_id = 456
        update.effective_message.migrate_from_chat_id = None
        update.effective_message.left_chat_member = None
        update.effective_message.new_chat_members = None

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        context = MagicMock()
        context.bot = bot

        with (
            patch("tg.handlers.messages.fallback._on_migrate") as mock_mig,
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            await handle_fallback_message(update, context)
            mock_mig.assert_called_once_with(update.effective_message.chat_id, 456)

    @pytest.mark.asyncio
    async def test_handle_fallback_migrate_from(self):
        update = MagicMock()
        update.effective_message.migrate_from_chat_id = 123
        update.effective_message.migrate_to_chat_id = None
        update.effective_message.left_chat_member = None
        update.effective_message.new_chat_members = None

        bot = MagicMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="me"))
        context = MagicMock()
        context.bot = bot

        with (
            patch("tg.handlers.messages.fallback._on_migrate") as mock_mig,
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            await handle_fallback_message(update, context)
            mock_mig.assert_called_once_with(123, update.effective_message.chat_id)

    def test_on_kick(self):
        with (
            patch("services.user_repo.load", return_value=User(chat_id=123)),
            patch("services.user_repo.save") as mock_save,
        ):
            _on_kick(123)
            mock_save.assert_called_once()

    def test_on_kick_no_user(self):
        with (
            patch("services.user_repo.load", return_value=None),
            patch("services.user_repo.save") as mock_save,
        ):
            _on_kick(123)
            mock_save.assert_not_called()

    def test_on_migrate(self):
        _on_migrate(123, 456)
