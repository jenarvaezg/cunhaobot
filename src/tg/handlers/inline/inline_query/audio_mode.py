import random
from telegram import InlineQueryResultVoice

from models.phrase import LongPhrase, Phrase
from tg.text_router import LONG_MODE, SHORT_MODE, get_query_mode


from .long_mode import get_long_mode_results  # noqa: F401
from .short_mode import get_short_mode_results  # noqa: F401

phrase_t = Phrase | LongPhrase


def _phrase_to_inline_audio(
    phrase: phrase_t, result_type: str
) -> InlineQueryResultVoice | None:
    from services import tts_service

    audio_url = tts_service.get_audio_url(phrase, result_type)
    if not audio_url:
        return None

    identifier = phrase.id if phrase.id is not None else phrase.text
    result_id = f"audio-{result_type}-{identifier}"
    return InlineQueryResultVoice(
        id=result_id[:63],
        voice_url=audio_url,
        title=phrase.text,
    )


def get_audio_mode_results(input: str) -> list[InlineQueryResultVoice]:
    from services import phrase_repo, long_phrase_repo

    mode, rest = get_query_mode(input)

    phrases = []
    if mode == SHORT_MODE:
        all_phrases = phrase_repo.load_all()
        random.shuffle(all_phrases)
        phrases = all_phrases[:10]  # Limit to 10 phrases
    elif mode == LONG_MODE:
        all_phrases = long_phrase_repo.load_all()
        random.shuffle(all_phrases)
        phrases = all_phrases[:10]  # Limit to 10 phrases

    results = []
    for p in phrases:
        if mode == SHORT_MODE:
            if res := _phrase_to_inline_audio(p, "short"):
                results.append(res)
        elif mode == LONG_MODE:
            if res := _phrase_to_inline_audio(p, "long"):
                results.append(res)
    return results
