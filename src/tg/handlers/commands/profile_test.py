import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import constants
from tg.handlers.commands.profile import handle_profile
from test_factories import PhraseFactory


@pytest.mark.asyncio
async def test_handle_profile_not_found(mock_container):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "test"
    update.effective_message.from_user.id = 123
    update.effective_message.reply_text = AsyncMock()
    update.to_dict.return_value = {}
    context = MagicMock()

    mock_container["user_service"].get_user.return_value = None
    mock_container["phrase_service"].get_random.return_value = PhraseFactory.build(
        text="fiera"
    )
    mock_container["usage_service"].log_usage.return_value = []

    await handle_profile(update, context)

    # Check for at least one call
    assert update.effective_message.reply_text.call_count >= 1
    call_args_list = update.effective_message.reply_text.call_args_list
    found = False
    for call_obj in call_args_list:
        args, _ = call_obj
        if "Todavía no tengo tu ficha" in args[0] and "fiera" in args[0]:
            found = True
            break
    assert found


@pytest.mark.asyncio
async def test_handle_profile_success(mock_container):
    with (
        patch("tg.handlers.commands.profile.config") as mock_config,
        patch("tg.handlers.commands.profile.notify_new_badges", new_callable=AsyncMock),
    ):
        update = MagicMock()
        update.effective_user.id = 123
        update.effective_user.name = "Test"
        update.effective_user.username = "test"
        update.effective_message.from_user.id = 123
        update.effective_message.reply_text = AsyncMock()
        update.to_dict.return_value = {}
        context = MagicMock()

        user = MagicMock()
        user.id = "user_123"
        user.name = "Paco"
        user.points = 500
        mock_container["user_service"].get_user.return_value = user

        mock_container["usage_service"].log_usage.return_value = []

        # The handler consumes one coherent Perfil summary from ProfileService.
        badge = MagicMock()
        badge.name = "Madrugador"
        badge.icon = "🌅"
        badge.description = "Test"
        summary = MagicMock()
        summary.points = 500
        summary.stats = {"total_usages": 10}
        summary.earned_badges = [badge]
        mock_container["profile_service"].get_profile_summary.return_value = summary

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
