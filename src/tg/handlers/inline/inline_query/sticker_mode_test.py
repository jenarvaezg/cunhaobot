from unittest.mock import patch
from tg.handlers.inline.inline_query.sticker_mode import get_sticker_mode_results
from models.phrase import Phrase, LongPhrase
from tg.text_router import SHORT_MODE, LONG_MODE


def test_get_sticker_mode_results_short():
    p1 = Phrase(text="foo", sticker_file_id="123", id=1)
    with (
        patch("services.phrase_repo.load_all", return_value=[p1]),
        patch(
            "tg.handlers.inline.inline_query.sticker_mode.get_query_mode",
            return_value=(SHORT_MODE, "rest"),
        ),
    ):
        results = get_sticker_mode_results("input")
        assert len(results) == 1
        assert results[0].sticker_file_id == "123"


def test_get_sticker_mode_results_long():
    p1 = LongPhrase(text="bar", sticker_file_id="456", id=2)
    with (
        patch("services.long_phrase_repo.get_phrases", return_value=[p1]),
        patch(
            "tg.handlers.inline.inline_query.sticker_mode.get_query_mode",
            return_value=(LONG_MODE, "rest"),
        ),
    ):
        results = get_sticker_mode_results("input")
        assert len(results) == 1
        assert results[0].sticker_file_id == "456"


def test_get_sticker_mode_results_other():
    with patch(
        "tg.handlers.inline.inline_query.sticker_mode.get_query_mode",
        return_value=("OTHER", ""),
    ):
        results = get_sticker_mode_results("input")
        assert results == []
