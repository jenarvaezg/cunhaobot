from unittest.mock import patch
from tg.handlers.inline.inline_query.short_mode import get_short_mode_results
from models.phrase import Phrase


def test_get_short_mode_results_empty():
    p1 = Phrase(text="foo")
    with (
        patch("services.phrase_repo.load_all", return_value=[p1]),
        patch(
            "tg.handlers.inline.inline_query.short_mode.get_thumb", return_value="thumb"
        ),
    ):
        results = get_short_mode_results("")
        assert len(results) > 0
        assert "foo" in results[0].title


def test_get_short_mode_results_with_size():
    p1 = Phrase(text="foo")
    p2 = Phrase(text="bar")
    with (
        patch("services.phrase_repo.load_all", return_value=[p1, p2]),
        patch(
            "tg.handlers.inline.inline_query.short_mode.get_thumb", return_value="thumb"
        ),
    ):
        results = get_short_mode_results("2")
        assert len(results) > 0
        # Combination of 2 phrases


def test_get_short_mode_results_with_finisher():
    p1 = Phrase(text="foo")
    with (
        patch("services.phrase_repo.load_all", return_value=[p1]),
        patch(
            "tg.handlers.inline.inline_query.short_mode.get_thumb", return_value="thumb"
        ),
    ):
        results = get_short_mode_results("1 finisher")
        assert len(results) > 0
        assert "finisher" in results[0].title


def test_get_short_mode_results_no_phrases():
    with patch("services.phrase_repo.load_all", return_value=[]):
        results = get_short_mode_results("")
        assert results == []
