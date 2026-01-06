import pytest
from unittest.mock import patch, AsyncMock
from tg.handlers.inline.inline_query.short_mode import get_short_mode_results
from models.phrase import Phrase


@pytest.mark.asyncio
async def test_get_short_mode_results_empty():
    p1 = Phrase(text="foo")
    with (
        patch("tg.handlers.inline.inline_query.short_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.short_mode.get_thumb", return_value="thumb"
        ),
    ):
        mock_services.phrase_repo.load_all = AsyncMock(return_value=[p1])
        results = await get_short_mode_results("")
        assert len(results) > 0
        assert "foo" in results[0].title


@pytest.mark.asyncio
async def test_get_short_mode_results_with_size():
    p1 = Phrase(text="foo")
    p2 = Phrase(text="bar")
    with (
        patch("tg.handlers.inline.inline_query.short_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.short_mode.get_thumb", return_value="thumb"
        ),
    ):
        mock_services.phrase_repo.load_all = AsyncMock(return_value=[p1, p2])
        results = await get_short_mode_results("2")
        assert len(results) > 0
        # Combination of 2 phrases


@pytest.mark.asyncio
async def test_get_short_mode_results_with_search():
    p1 = Phrase(text="maquina")
    p2 = Phrase(text="figura")
    with (
        patch("tg.handlers.inline.inline_query.short_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.short_mode.get_thumb", return_value="thumb"
        ),
    ):
        mock_services.phrase_repo.load_all = AsyncMock(return_value=[p1, p2])
        results = await get_short_mode_results("maquina")
        assert len(results) > 0
        assert "maquina" in results[0].title
        assert "figura" not in results[0].title


@pytest.mark.asyncio
async def test_get_short_mode_results_no_results():
    p1 = Phrase(text="foo")
    with (
        patch("tg.handlers.inline.inline_query.short_mode.services") as mock_services,
        patch(
            "tg.handlers.inline.inline_query.short_mode.get_thumb", return_value="thumb"
        ),
    ):
        mock_services.phrase_repo.load_all = AsyncMock(return_value=[p1])
        results = await get_short_mode_results("notfound")
        assert len(results) == 1
        assert "No tengo" in results[0].title


@pytest.mark.asyncio
async def test_get_short_mode_results_no_phrases():
    with patch("tg.handlers.inline.inline_query.short_mode.services") as mock_services:
        mock_services.phrase_repo.load_all = AsyncMock(return_value=[])
        results = await get_short_mode_results("")
        assert results == []
