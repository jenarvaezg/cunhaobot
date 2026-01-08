import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.inline.inline_query.base import handle_inline_query


from test_factories import PhraseFactory


class TestInlineQuery:
    @pytest.mark.asyncio
    async def test_handle_inline_query_short(self, mock_container):
        update = MagicMock()
        user = MagicMock()
        user.id = 123
        user.name = "Test User"
        user.username = "testuser"

        chat = MagicMock()
        chat.id = 123
        chat.type = "private"
        chat.title = "Chat"

        update.effective_user = user
        update.effective_chat = chat
        update.inline_query.query = "short"
        update.inline_query.answer = AsyncMock()
        update.inline_query.from_user = user

        mock_container["phrase_repo"].load_all = AsyncMock(
            return_value=[PhraseFactory.build(text="p1")]
        )

        await handle_inline_query(update, MagicMock())
        update.inline_query.answer.assert_called_once()
        mock_container["user_service"].update_or_create_inline_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_inline_query_no_func(self, mock_container):
        update = MagicMock()
        user = MagicMock()
        user.id = 123
        user.name = "Test User"
        user.username = "testuser"

        chat = MagicMock()
        chat.id = 123
        chat.type = "private"
        chat.title = "Chat"

        update.effective_user = user
        update.effective_chat = chat
        update.inline_query.query = "!!"
        update.inline_query.answer = AsyncMock()

        mock_phrase = PhraseFactory.build(text="cuñao")
        mock_container["phrase_service"].get_random.return_value = mock_phrase

        with patch(
            "tg.handlers.inline.inline_query.base.get_query_mode",
            return_value=("", ""),
        ):
            await handle_inline_query(update, MagicMock())
            update.inline_query.answer.assert_called_once()
            results = update.inline_query.answer.call_args[0][0]
            assert "No sabes usarme" in results[0].title
