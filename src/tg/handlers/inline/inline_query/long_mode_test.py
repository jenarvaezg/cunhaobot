from unittest.mock import patch
from tg.handlers.inline.inline_query.long_mode import get_long_mode_results
from models.phrase import LongPhrase


def test_get_long_mode_results_success():
    p1 = LongPhrase(text="long phrase test", id=1)
    with (
        patch("services.long_phrase_repo.get_phrases", return_value=[p1]),
        patch(
            "tg.handlers.inline.inline_query.long_mode.get_thumb", return_value="thumb"
        ),
    ):
        results = get_long_mode_results("test")
        assert len(results) == 1
        assert results[0].title == "long phrase test"
        assert results[0].input_message_content.message_text == "long phrase test"


def test_get_long_mode_results_no_results():
    with (
        patch("services.long_phrase_repo.get_phrases", return_value=[]),
        patch(
            "tg.handlers.inline.inline_query.long_mode.phrase_service"
        ) as mock_service,
        patch(
            "tg.handlers.inline.inline_query.long_mode.get_thumb", return_value="thumb"
        ),
    ):
        mock_service.get_random.return_value.text = "random phrase"
        results = get_long_mode_results("search")
        assert len(results) == 1
        assert results[0].input_message_content.message_text == "random phrase"
        assert "No hay resultados" in results[0].title
