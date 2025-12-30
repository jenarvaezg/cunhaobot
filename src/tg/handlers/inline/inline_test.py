import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.inline.inline_query.base import handle_inline_query
from services.user_service import UserService  # Import the class
from models.phrase import Phrase  # Import Phrase to mock correctly


class TestInlineQuery:
    @pytest.mark.asyncio
    async def test_handle_inline_query_short(self):
        update = MagicMock()
        update.inline_query.query = "short"
        update.inline_query.answer = AsyncMock()
        update.effective_user.id = 123
        update.effective_user.name = "Test User"  # Provide a string value

        with (
            patch("services.phrase_repo.load_all", return_value=[MagicMock(text="p1")]),
            patch.object(
                UserService, "update_or_create_inline_user"
            ) as mock_update_inline_user,
            patch.object(
                UserService, "update_or_create_user"
            ) as mock_update_user,  # Patch the decorator's call
        ):
            await handle_inline_query(update, MagicMock())
            update.inline_query.answer.assert_called_once()
            mock_update_inline_user.assert_called_once()
            mock_update_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_inline_query_no_func(self):
        update = MagicMock()
        update.inline_query.query = "unknown_mode"
        update.inline_query.answer = AsyncMock()
        update.effective_user.id = 123
        update.effective_user.name = "Test User"  # Provide a string value

        mock_phrase = Phrase(text="cuñao")
        with (
            patch.object(
                UserService, "update_or_create_user"
            ) as mock_update_user,  # Patch the decorator's call
            patch(
                "tg.handlers.inline.inline_query.base.phrase_service.get_random",
                return_value=mock_phrase,
            ),  # Patch phrase_service.get_random
        ):
            await handle_inline_query(update, MagicMock())
            update.inline_query.answer.assert_called_once()
            # Should answer with help/dont know how to use
            results = update.inline_query.answer.call_args[0][0]
            assert "No sabes usarme" in results[0].title
            mock_update_user.assert_called_once()
