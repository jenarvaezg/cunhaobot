from telegram import InlineQueryResultVoice

from models.phrase import LongPhrase, Phrase
from tg.text_router import LONG_MODE, SHORT_MODE, get_query_mode
from utils.gcp import get_audio_url


phrase_t = Phrase | LongPhrase


def _phrase_to_inline_audio(
    phrase: phrase_t, result_type: str
) -> InlineQueryResultVoice | None:
    file_name = f"{result_type}-{phrase.text}"
    audio_url = get_audio_url(file_name)
    if not audio_url:
        return None

    result_id = f"audio-{result_type}-{phrase.text}"
    return InlineQueryResultVoice(
        id=result_id[:63],
        voice_url=audio_url,
        title=phrase.text,
    )


def get_audio_mode_results(input: str) -> list[InlineQueryResultVoice]:
    mode, rest = get_query_mode(input)

    results = []
    if mode == SHORT_MODE:
        results = [
            res
            for p in Phrase.get_phrases()
            if (res := _phrase_to_inline_audio(p, "short"))
        ]
    elif mode == LONG_MODE:
        results = [
            res
            for p in LongPhrase.get_phrases()
            if (res := _phrase_to_inline_audio(p, "long"))
        ]

    return results
