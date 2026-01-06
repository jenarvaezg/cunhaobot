import random
from typing import cast
from telegram import InlineQueryResultVoice

from models.phrase import LongPhrase, Phrase
from core.container import services
from tg.text_router import LONG_MODE, SHORT_MODE, get_query_mode


def _phrase_to_inline_audio(
    phrase: Phrase | LongPhrase, result_type: str
) -> InlineQueryResultVoice | None:
    audio_url = services.tts_service.get_audio_url(phrase, result_type)
    if not audio_url or phrase.id is None:
        return None

    result_id = f"audio-{result_type}-{phrase.id}"
    return InlineQueryResultVoice(
        id=result_id[:63],
        voice_url=audio_url,
        title=phrase.text,
    )


async def get_audio_mode_results(input: str) -> list[InlineQueryResultVoice]:
    mode, rest = get_query_mode(input)

    phrases: list[Phrase | LongPhrase] = []
    result_type = "short"
    if mode == SHORT_MODE:
        result_type = "short"
        phrases = cast(
            list[Phrase | LongPhrase],
            await services.phrase_repo.get_phrases(search=rest),
        )
    elif mode == LONG_MODE:
        result_type = "long"
        phrases = cast(
            list[Phrase | LongPhrase],
            await services.long_phrase_repo.get_phrases(search=rest),
        )

    random.shuffle(phrases)

    results: list[InlineQueryResultVoice] = []
    for p in phrases:
        if res := _phrase_to_inline_audio(p, result_type):
            results.append(res)
        if len(results) >= 10:
            break
    return results
