import pytest
from unittest.mock import MagicMock, patch
from tg.handlers.inline.chosen_inine_result import handle_chosen_inline_result


@pytest.mark.asyncio
async def test_handle_chosen_inline_result_success():
    update = MagicMock()
    update.chosen_inline_result.result_id = "short-test"

    with (
        patch(
            "tg.handlers.inline.chosen_inine_result.user_service"
        ) as mock_user_service,
        patch(
            "tg.handlers.inline.chosen_inine_result.phrase_service"
        ) as mock_phrase_service,
        patch("tg.decorators.user_service.update_or_create_user"),  # For log_update
    ):
        mock_user = MagicMock()
        mock_user_service.update_or_create_inline_user.return_value = mock_user

        await handle_chosen_inline_result(update, MagicMock())

        mock_user_service.update_or_create_inline_user.assert_called_once_with(update)
        mock_user_service.add_inline_usage.assert_called_once_with(mock_user)
        mock_phrase_service.add_usage_by_id.assert_called_once_with("short-test")


@pytest.mark.asyncio
async def test_handle_chosen_inline_result_no_result():
    update = MagicMock()
    update.chosen_inline_result = None

    with (
        patch(
            "tg.handlers.inline.chosen_inine_result.user_service"
        ) as mock_user_service,
        patch(
            "tg.handlers.inline.chosen_inine_result.phrase_service"
        ) as mock_phrase_service,
        patch("tg.decorators.user_service.update_or_create_user"),
    ):
        mock_user_service.update_or_create_inline_user.return_value = None

        await handle_chosen_inline_result(update, MagicMock())

        mock_user_service.add_inline_usage.assert_not_called()
        mock_phrase_service.add_usage_by_id.assert_not_called()
