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
            patch(
                "services.phrase_repo.load_all",
                new_callable=AsyncMock,
                return_value=[MagicMock(text="p1")],
            ),
            patch.object(
                UserService, "update_or_create_inline_user", new_callable=AsyncMock
            ) as mock_update_inline_user,
            patch.object(
                UserService, "update_or_create_user", new_callable=AsyncMock
            ),  # Patch the decorator's call
        ):
            await handle_inline_query(update, MagicMock())
            update.inline_query.answer.assert_called_once()
            mock_update_inline_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_inline_query_no_func(self):
        update = MagicMock()
        update.inline_query.query = "!!"  # Use symbols to trigger no-mode logic (now actually defaults to long if not numeric/empty)
        # Actually, if I want to trigger the "results_func is None" branch,
        # I need get_query_mode to return ("", "").
        # But my new get_query_mode is very broad.
        # Let's mock get_query_mode directly for this test.
        update.inline_query.answer = AsyncMock()
        update.effective_user.id = 123
        update.effective_user.name = "Test User"

        mock_phrase = Phrase(text="cuñao")
        with (
            patch(
                "tg.handlers.inline.inline_query.base.get_query_mode",
                return_value=("", ""),
            ),
            patch.object(UserService, "update_or_create_user", new_callable=AsyncMock),
            patch(
                "tg.handlers.inline.inline_query.base.phrase_service.get_random",
                new_callable=AsyncMock,
                return_value=mock_phrase,
            ),
        ):
            await handle_inline_query(update, MagicMock())
            update.inline_query.answer.assert_called_once()
            results = update.inline_query.answer.call_args[0][0]
            assert "No sabes usarme" in results[0].title
