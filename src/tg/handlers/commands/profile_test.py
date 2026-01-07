import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import constants

# To avoid circular imports when testing tg handlers,
# we often need to patch services before importing the handler
# OR use local patches inside the test functions.


@pytest.mark.asyncio
async def test_handle_profile_not_found():
    with patch("tg.handlers.commands.profile.services") as mock_services:
        # Avoid circular import by importing inside the test
        from tg.handlers.commands.profile import handle_profile

        update = MagicMock()
        update.effective_message.from_user.id = 123
        update.effective_message.reply_text = AsyncMock()
        update.to_dict.return_value = {}
        context = MagicMock()

        mock_services.user_service.get_user = AsyncMock(return_value=None)
        mock_services.phrase_service.get_random = AsyncMock(
            return_value=MagicMock(text="fiera")
        )

        await handle_profile(update, context)

        update.effective_message.reply_text.assert_called_once()
        args, _ = update.effective_message.reply_text.call_args
        assert "Todavía no tengo tu ficha" in args[0]
        assert "fiera" in args[0]


@pytest.mark.asyncio
async def test_handle_profile_success():
    with (
        patch("tg.handlers.commands.profile.services") as mock_services,
        patch("tg.handlers.commands.profile.config") as mock_config,
        patch("tg.handlers.commands.profile.notify_new_badges", new_callable=AsyncMock),
    ):
        from tg.handlers.commands.profile import handle_profile

        update = MagicMock()
        update.effective_message.from_user.id = 123
        update.effective_message.reply_text = AsyncMock()
        update.to_dict.return_value = {}
        context = MagicMock()

        user = MagicMock()
        user.id = "user_123"
        user.name = "Paco"
        user.points = 500
        mock_services.user_service.get_user = AsyncMock(return_value=user)

        mock_services.usage_service.log_usage = AsyncMock(return_value=[])
        mock_services.usage_service.get_user_stats = AsyncMock(
            return_value={"total_usages": 10}
        )

        badge_progress = MagicMock()
        badge_progress.is_earned = True
        badge_progress.badge.name = "Madrugador"
        badge_progress.badge.icon = "🌅"
        badge_progress.badge.description = "Test"
        mock_services.badge_service.get_all_badges_progress = AsyncMock(
            return_value=[badge_progress]
        )

        mock_config.base_url = "http://test.com"

        await handle_profile(update, context)

        update.effective_message.reply_text.assert_called_once()
        args, kwargs = update.effective_message.reply_text.call_args
        text = args[0]
        assert "Perfil de Paco" in text
        assert "500" in text
        assert "Madrugador" in text
        assert "🌅" in text
        assert kwargs["parse_mode"] == constants.ParseMode.HTML
