import random
from telegram import InlineQueryResultVoice

from models.phrase import LongPhrase, Phrase
from tg.text_router import LONG_MODE, SHORT_MODE, get_query_mode


phrase_t = Phrase | LongPhrase


def _phrase_to_inline_audio(
    phrase: phrase_t, result_type: str
) -> InlineQueryResultVoice | None:
    from services import tts_service

    audio_url = tts_service.get_audio_url(phrase, result_type)
    if not audio_url or phrase.id is None:
        return None

    result_id = f"audio-{result_type}-{phrase.id}"
    return InlineQueryResultVoice(
        id=result_id[:63],
        voice_url=audio_url,
        title=phrase.text,
    )


async def get_audio_mode_results(input: str) -> list[InlineQueryResultVoice]:
    from services import phrase_repo, long_phrase_repo

    mode, rest = get_query_mode(input)

    phrases = []
    result_type = "short"
    if mode == SHORT_MODE:
        result_type = "short"
        phrases = await phrase_repo.get_phrases(search=rest)
    elif mode == LONG_MODE:
        result_type = "long"
        phrases = await long_phrase_repo.get_phrases(search=rest)

    random.shuffle(phrases)

    results = []
    for p in phrases:
        if res := _phrase_to_inline_audio(p, result_type):
            results.append(res)
        if len(results) >= 10:
            break
    return results
