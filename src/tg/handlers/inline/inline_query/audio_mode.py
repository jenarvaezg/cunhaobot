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

    result_id = f"audio-{result_type}-{phrase.text}"
    return InlineQueryResultVoice(
        id=result_id[:63],
        voice_url=audio_url,
        title=phrase.text,
    )


def get_audio_mode_results(input: str) -> list[InlineQueryResultVoice]:
    from services import phrase_repo, long_phrase_repo

    mode, rest = get_query_mode(input)

    results = []
    if mode == SHORT_MODE:
        results = [
            res
            for p in phrase_repo.load_all()
            if (res := _phrase_to_inline_audio(p, "short"))
        ]
    elif mode == LONG_MODE:
        results = [
            res
            for p in long_phrase_repo.load_all()
            if (res := _phrase_to_inline_audio(p, "long"))
        ]

    return results
