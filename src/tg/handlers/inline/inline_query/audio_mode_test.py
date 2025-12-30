from unittest.mock import patch
from tg.handlers.inline.inline_query.audio_mode import get_audio_mode_results
from models.phrase import Phrase, LongPhrase
from tg.text_router import SHORT_MODE, LONG_MODE


def test_get_audio_mode_results_short():
    p1 = Phrase(text="foo")
    with (
        patch("services.phrase_repo.load_all", return_value=[p1]),
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_audio_url",
            return_value="http://audio",
        ) as mock_url,
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
            return_value=(SHORT_MODE, "rest"),
        ),
    ):
        results = get_audio_mode_results("input")
        assert len(results) == 1
        assert results[0].voice_url == "http://audio"
        assert results[0].title == "foo"
        mock_url.assert_called_once_with("short-foo")


def test_get_audio_mode_results_long():
    p1 = LongPhrase(text="bar")
    with (
        patch("services.long_phrase_repo.load_all", return_value=[p1]),
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_audio_url",
            return_value="http://audio",
        ),
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
            return_value=(LONG_MODE, "rest"),
        ),
    ):
        results = get_audio_mode_results("input")
        assert len(results) == 1
        assert results[0].title == "bar"


def test_get_audio_mode_results_no_url():
    p1 = Phrase(text="foo")
    with (
        patch("services.phrase_repo.load_all", return_value=[p1]),
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_audio_url",
            return_value=None,
        ),
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
            return_value=(SHORT_MODE, "rest"),
        ),
    ):
        results = get_audio_mode_results("input")
        assert len(results) == 0


def test_get_audio_mode_results_other_mode():
    with patch(
        "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
        return_value=("OTHER", ""),
    ):
        results = get_audio_mode_results("input")
        assert results == []
