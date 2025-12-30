import random

from telegram import InlineQueryResultCachedSticker

from models.phrase import LongPhrase, Phrase
from tg.text_router import LONG_MODE, SHORT_MODE, get_query_mode
from utils import normalize_str

phrase_t = Phrase | LongPhrase


def _phrase_to_inline_sticker(
    phrase: phrase_t, result_type: str
) -> InlineQueryResultCachedSticker:
    result_id = f"sticker-{result_type}-{normalize_str(phrase.text)}"
    return InlineQueryResultCachedSticker(
        id=result_id[:63], sticker_file_id=phrase.sticker_file_id
    )


def get_sticker_mode_results(input: str) -> list[InlineQueryResultCachedSticker]:
    from services import phrase_repo, long_phrase_repo

    mode, rest = get_query_mode(input)

    phrases = []
    result_type = ""
    if mode == SHORT_MODE:
        result_type = "short"
        phrases = phrase_repo.load_all()
    elif mode == LONG_MODE:
        result_type = "long"
        phrases = long_phrase_repo.get_phrases(search=normalize_str(rest))

    random.shuffle(phrases)
    return [_phrase_to_inline_sticker(p, result_type) for p in phrases[:10]]
