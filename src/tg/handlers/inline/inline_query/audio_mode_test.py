import pytest
from unittest.mock import patch, AsyncMock
from tg.handlers.inline.inline_query.audio_mode import get_audio_mode_results
from models.phrase import Phrase, LongPhrase
from tg.text_router import SHORT_MODE, LONG_MODE


@pytest.mark.asyncio
async def test_get_audio_mode_results_short():
    p1 = Phrase(text="foo", id=1)
    with (
        patch("tg.handlers.inline.inline_query.audio_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
            return_value=(SHORT_MODE, "rest"),
        ),
    ):
        mock_services.phrase_repo.get_phrases = AsyncMock(return_value=[p1])
        mock_services.tts_service.get_audio_url.return_value = "http://audio"

        results = await get_audio_mode_results("input")
        assert len(results) == 1
        assert results[0].voice_url == "http://audio"
        assert results[0].title == "foo"
        mock_services.tts_service.get_audio_url.assert_called_once_with(p1, "short")


@pytest.mark.asyncio
async def test_get_audio_mode_results_long():
    p1 = LongPhrase(text="bar", id=2)
    with (
        patch("tg.handlers.inline.inline_query.audio_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
            return_value=(LONG_MODE, "rest"),
        ),
    ):
        mock_services.long_phrase_repo.get_phrases = AsyncMock(return_value=[p1])
        mock_services.tts_service.get_audio_url.return_value = "http://audio"

        results = await get_audio_mode_results("input")
        assert len(results) == 1
        assert results[0].title == "bar"


@pytest.mark.asyncio
async def test_get_audio_mode_results_no_url():
    p1 = Phrase(text="foo", id=1)
    with (
        patch("tg.handlers.inline.inline_query.audio_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
            return_value=(SHORT_MODE, "rest"),
        ),
    ):
        mock_services.phrase_repo.get_phrases = AsyncMock(return_value=[p1])
        mock_services.tts_service.get_audio_url.return_value = None

        results = await get_audio_mode_results("input")
        assert len(results) == 0


@pytest.mark.asyncio
async def test_get_audio_mode_results_other_mode():
    with patch(
        "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
        return_value=("OTHER", ""),
    ):
        results = await get_audio_mode_results("input")
        assert results == []


@pytest.mark.asyncio
async def test_get_audio_mode_results_search():
    p1 = LongPhrase(text="facha", id=1)
    with (
        patch("tg.handlers.inline.inline_query.audio_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.audio_mode.get_query_mode",
            return_value=(LONG_MODE, "facha"),
        ),
    ):
        mock_services.long_phrase_repo.get_phrases = AsyncMock(return_value=[p1])
        mock_services.tts_service.get_audio_url.return_value = "http://audio"

        results = await get_audio_mode_results("audio facha")
        assert len(results) == 1
        assert results[0].title == "facha"
        mock_services.long_phrase_repo.get_phrases.assert_called_once_with(
            search="facha"
        )
