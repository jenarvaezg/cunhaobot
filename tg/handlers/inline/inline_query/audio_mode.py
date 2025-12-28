from typing import Optional

from telegram import InlineQueryResultArticle, InlineQueryResultVoice

from tg.text_router import LONG_MODE, SHORT_MODE, get_query_mode
from utils import normalize_str
from utils.gcp import get_audio_url

from .long_mode import get_long_mode_results
from .short_mode import get_short_mode_results


def short_result_to_audio_result(
    result: InlineQueryResultArticle,
) -> Optional[InlineQueryResultVoice]:
    title = result.title
    clean_title = title.replace(",", "").replace(" ", "")
    audio_url = get_audio_url(clean_title)
    if not audio_url:
        return None

    result_id = f"audio-{result.id}"
    return InlineQueryResultVoice(
        result_id[:63],
        audio_url,
        title,
    )


def long_result_to_audio_result(
    result: InlineQueryResultArticle,
) -> Optional[InlineQueryResultVoice]:
    title = result.title
    audio_url = get_audio_url(title)
    if not audio_url:
        return None

    result_id = normalize_str(f"audio-{result.id}")
    return InlineQueryResultVoice(
        result_id[:63],
        audio_url,
        title,
    )


def get_audio_mode_results(input: str) -> list:
    mode, rest = get_query_mode(input)

    results = []
    if mode == SHORT_MODE:
        results = [
            short_result_to_audio_result(result)
            for result in get_short_mode_results(rest)[:5]
            if result.title
        ]
    elif mode == LONG_MODE:
        results = [
            long_result_to_audio_result(result)
            for result in get_long_mode_results(rest)
        ]

    # Filter out None results where audio was not found
    return [r for r in results if r is not None]
