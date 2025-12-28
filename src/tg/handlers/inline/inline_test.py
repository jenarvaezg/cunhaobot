import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.inline.inline_query.base import handle_inline_query
from tg.handlers.inline.inline_query.short_mode import get_short_mode_results
from tg.handlers.inline.inline_query.long_mode import get_long_mode_results
from tg.handlers.inline.inline_query.sticker_mode import get_sticker_mode_results
from tg.handlers.inline.inline_query.audio_mode import get_audio_mode_results
from tg.handlers.inline.chosen_inine_result import handle_chosen_inline_result
from models.phrase import Phrase, LongPhrase


class TestInlineQuery:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        # Mock Phrase.get_random_phrase
        self.patcher_phrase = patch(
            "models.phrase.Phrase.get_random_phrase", return_value="cuñao"
        )
        self.mock_phrase = self.patcher_phrase.start()
        from models.phrase import Phrase, LongPhrase

        Phrase.phrases_cache = [Phrase(text="p1")]
        LongPhrase.phrases_cache = [LongPhrase(text="lp1")]
        mock_datastore_client.reset_mock()
        # Ensure refresh_cache doesn't crash if called
        mock_datastore_client.query.return_value.fetch.return_value = []
        yield
        self.patcher_phrase.stop()

    @pytest.mark.asyncio
    async def test_handle_inline_query_short(self):
        update = MagicMock()
        update.inline_query.query = "short test"
        update.inline_query.answer = AsyncMock()
        update.effective_user.id = 123
        update.effective_user.name = "test"

        with (
            patch(
                "tg.handlers.inline.inline_query.base.get_query_mode",
                return_value=("SHORT", "test"),
            ),
            patch(
                "tg.handlers.inline.inline_query.base.MODE_HANDLERS",
                {"SHORT": lambda x: ["result"]},
            ),
            patch("models.user.InlineUser.update_or_create_from_update"),
        ):
            await handle_inline_query(update, MagicMock())
            update.inline_query.answer.assert_called_once()

    def test_get_short_mode_results(self):
        p1 = Phrase(text="phrase1")
        with patch("models.phrase.Phrase.get_phrases", return_value=[p1]):
            results = get_short_mode_results("1 test")
            assert len(results) > 0
            assert "short-" in results[0].id

    def test_get_long_mode_results(self):
        lp1 = LongPhrase(text="long phrase one")
        with patch("models.phrase.LongPhrase.get_phrases", return_value=[lp1]):
            results = get_long_mode_results("test")
            assert len(results) > 0
            assert results[0].id.startswith("long-")

    def test_get_sticker_mode_results(self):
        p1 = Phrase(text="phrase1", sticker_file_id="file123")
        with patch("models.phrase.Phrase.get_phrases", return_value=[p1]):
            results = get_sticker_mode_results("test")
            assert len(results) > 0
            assert results[0].id.startswith("sticker-")

    def test_get_audio_mode_results_short(self):
        # Mock result from get_short_mode_results
        mock_short_res = MagicMock()
        mock_short_res.title = "p1, p2"
        mock_short_res.id = "short-p1p2"
        mock_short_res.input_message_content.message_text = "p1, p2"

        with (
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
                return_value=("SHORT", "test"),
            ),
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_short_mode_results",
                return_value=[mock_short_res],
            ),
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_audio_url",
                return_value="http://url",
            ),
        ):
            results = get_audio_mode_results("audio test")
            assert len(results) > 0
            assert "audio" in results[0].id

    def test_get_audio_mode_results_short_no_url(self):
        mock_short_res = MagicMock()
        mock_short_res.title = "p1, p2"
        mock_short_res.id = "short-p1p2"
        mock_short_res.input_message_content.message_text = "p1, p2"

        with (
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
                return_value=("SHORT", "test"),
            ),
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_short_mode_results",
                return_value=[mock_short_res],
            ),
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_audio_url",
                return_value=None,
            ),
        ):
            results = get_audio_mode_results("audio test")
            assert len(results) == 0

    def test_get_audio_mode_results_long(self):
        mock_long_res = MagicMock()
        mock_long_res.title = "long title"
        mock_long_res.id = "long-id"
        mock_long_res.input_message_content.message_text = "long text"

        with (
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
                return_value=("LONG", "test"),
            ),
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_long_mode_results",
                return_value=[mock_long_res],
            ),
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_audio_url",
                return_value="http://url",
            ),
        ):
            results = get_audio_mode_results("audio frase test")
            assert len(results) > 0
            assert "audio" in results[0].id

    def test_get_audio_mode_results_long_no_url(self):
        mock_long_res = MagicMock()
        mock_long_res.title = "long title"
        mock_long_res.id = "long-id"
        mock_long_res.input_message_content.message_text = "long text"

        with (
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
                return_value=("LONG", "test"),
            ),
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_long_mode_results",
                return_value=[mock_long_res],
            ),
            patch(
                "tg.handlers.inline.inline_query.audio_mode.get_audio_url",
                return_value=None,
            ),
        ):
            results = get_audio_mode_results("audio frase test")
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_handle_chosen_inline_result_long_prefix(self):
        # From last_push_test.py
        update = MagicMock()
        update.chosen_inline_result.result_id = "long-phrase-123"
        context = MagicMock()

        with (
            patch(
                "models.user.InlineUser.update_or_create_from_update"
            ) as mock_user_get,
            patch("models.phrase.LongPhrase.add_usage_by_result_id") as mock_add_usage,
        ):
            mock_user = MagicMock()
            mock_user_get.return_value = mock_user

            await handle_chosen_inline_result(update, context)
            mock_add_usage.assert_called_with("long-phrase-123")

    @pytest.mark.asyncio
    async def test_handle_chosen_inline_result_short(self):
        # From misc_handlers_test.py
        update = MagicMock()
        update.chosen_inline_result.result_id = "short-test"
        context = MagicMock()

        with (
            patch(
                "models.user.InlineUser.update_or_create_from_update"
            ) as mock_user_get,
            patch("models.phrase.Phrase.add_usage_by_result_id") as mock_add_usage,
        ):
            mock_user = MagicMock()
            mock_user_get.return_value = mock_user

            await handle_chosen_inline_result(update, context)
            mock_user.add_usage.assert_called_once()
            mock_add_usage.assert_called_with("short-test")

    @pytest.mark.asyncio
    async def test_handle_chosen_inline_result_long(self):
        # From misc_handlers_test.py
        update = MagicMock()
        update.chosen_inline_result.result_id = "long-test"
        context = MagicMock()

        with (
            patch(
                "models.user.InlineUser.update_or_create_from_update"
            ) as mock_user_get,
            patch("models.phrase.LongPhrase.add_usage_by_result_id") as mock_add_usage,
        ):
            mock_user = MagicMock()
            mock_user_get.return_value = mock_user

            await handle_chosen_inline_result(update, context)
            mock_add_usage.assert_called_with("long-test")

    @pytest.mark.asyncio
    async def test_handle_chosen_inline_result_no_data(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.chosen_inline_result = None
        await handle_chosen_inline_result(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_chosen_inline_result_no_user(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.chosen_inline_result.result_id = "short-test"
        with patch(
            "models.user.InlineUser.update_or_create_from_update", return_value=None
        ):
            await handle_chosen_inline_result(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_inline_query_no_func(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.inline_query.query = "unknown_mode rest"
        update.inline_query.answer = AsyncMock()

        with patch(
            "tg.handlers.inline.inline_query.base.get_query_mode",
            return_value=("UNKNOWN", "rest"),
        ):
            await handle_inline_query(update, MagicMock())
            update.inline_query.answer.assert_called()

    def test_get_long_mode_results_empty(self):
        # From missing_lines_test.py
        p1 = LongPhrase(text="lp1")
        with (
            patch("models.phrase.LongPhrase.get_phrases", side_effect=[[], [p1]]),
            patch("models.phrase.LongPhrase.get_random_phrase", return_value=p1),
        ):
            res = get_long_mode_results("search")
            assert len(res) == 1
            assert "-bad-search-" in res[0].id

    def test_get_short_mode_results_empty_input(self):
        # From missing_lines_test.py
        res = get_short_mode_results("")
        assert len(res) > 0

    def test_get_sticker_mode_results_short(self):
        # From missing_lines_test.py
        res = get_sticker_mode_results("short rest")
        assert len(res) > 0

    def test_get_sticker_mode_results_empty(self):
        # From missing_lines_test.py
        with patch("models.phrase.Phrase.get_phrases", return_value=[]):
            res = get_sticker_mode_results("short search")
            assert len(res) == 0
