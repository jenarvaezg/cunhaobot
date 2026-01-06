import pytest
from unittest.mock import patch, AsyncMock
from tg.handlers.inline.inline_query.sticker_mode import get_sticker_mode_results
from models.phrase import Phrase, LongPhrase
from tg.text_router import SHORT_MODE, LONG_MODE


@pytest.mark.asyncio
async def test_get_sticker_mode_results_short():
    p1 = Phrase(text="foo", sticker_file_id="123", id=1)
    with (
        patch("tg.handlers.inline.inline_query.sticker_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.sticker_mode.get_query_mode",
            return_value=(SHORT_MODE, "rest"),
        ),
    ):
        mock_services.phrase_repo.get_phrases = AsyncMock(return_value=[p1])
        results = await get_sticker_mode_results("input")
        assert len(results) == 1
        assert results[0].sticker_file_id == "123"


@pytest.mark.asyncio
async def test_get_sticker_mode_results_long():
    p1 = LongPhrase(text="bar", sticker_file_id="456", id=2)
    with (
        patch("tg.handlers.inline.inline_query.sticker_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.sticker_mode.get_query_mode",
            return_value=(LONG_MODE, "rest"),
        ),
    ):
        mock_services.long_phrase_repo.get_phrases = AsyncMock(return_value=[p1])
        results = await get_sticker_mode_results("input")
        assert len(results) == 1
        assert results[0].sticker_file_id == "456"


@pytest.mark.asyncio
async def test_get_sticker_mode_results_other():
    with patch(
        "tg.handlers.inline.inline_query.sticker_mode.get_query_mode",
        return_value=("OTHER", ""),
    ):
        results = await get_sticker_mode_results("input")
        assert results == []
