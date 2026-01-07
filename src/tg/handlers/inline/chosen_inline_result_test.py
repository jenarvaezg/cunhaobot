import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.inline.chosen_inline_result import handle_chosen_inline_result


@pytest.mark.asyncio
async def test_handle_chosen_inline_result_success():
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.chosen_inline_result.result_id = "short-test"
    update.chosen_inline_result.from_user.id = 123
    update.chosen_inline_result.from_user.username = "testuser"

    with patch("tg.handlers.inline.chosen_inline_result.services") as mock_services:
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.name = "Test"
        mock_user.username = "test"
        mock_services.user_service.update_or_create_inline_user = AsyncMock(
            return_value=mock_user
        )
        mock_services.user_service.add_inline_usage = AsyncMock()
        mock_services.phrase_service.add_usage_by_id = AsyncMock()
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])
        mock_services.user_service.update_or_create_user = AsyncMock()

        await handle_chosen_inline_result(update, MagicMock())

        mock_services.user_service.update_or_create_inline_user.assert_called_once_with(
            update
        )
        mock_services.user_service.add_inline_usage.assert_called_once_with(mock_user)
        mock_services.phrase_service.add_usage_by_id.assert_called_once_with(
            "short-test"
        )


@pytest.mark.asyncio
async def test_handle_chosen_inline_result_no_result():
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.chosen_inline_result = None

    with patch("tg.handlers.inline.chosen_inline_result.services") as mock_services:
        mock_services.user_service.update_or_create_inline_user = AsyncMock(
            return_value=None
        )
        mock_services.user_service.add_inline_usage = AsyncMock()
        mock_services.phrase_service.add_usage_by_id = AsyncMock()
        mock_services.user_service.update_or_create_user = AsyncMock()

        await handle_chosen_inline_result(update, MagicMock())

        mock_services.user_service.add_inline_usage.assert_not_called()
        mock_services.phrase_service.add_usage_by_id.assert_not_called()
