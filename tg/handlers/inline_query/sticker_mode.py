import random
from typing import List, Union, Type

from telegram import InlineQueryResultCachedSticker

from models.phrase import LongPhrase, Phrase
from utils import normalize_str
from tg.text_router import get_query_mode, SHORT_MODE, LONG_MODE

phrase_t = Union[Phrase, LongPhrase]


def _phrase_to_inline_sticker(phrase: phrase_t, result_type: str) -> InlineQueryResultCachedSticker:
    result_id = f'sticker-{result_type}-{normalize_str(phrase.text)}'
    return InlineQueryResultCachedSticker(
        id=result_id[:63],
        sticker_file_id=phrase.sticker_file_id
    )


def get_sticker_mode_results(input: str) -> List[InlineQueryResultCachedSticker]:
    mode, rest = get_query_mode(input)

    result_type = ''
    phrases = []
    if mode == SHORT_MODE:
        result_type = 'short'
        phrases = Phrase.get_phrases()
    elif mode == LONG_MODE:
        result_type = 'long'
        phrases = LongPhrase.get_phrases(normalize_str(rest))

    random.shuffle(phrases)
    return [_phrase_to_inline_sticker(p, result_type) for p in phrases[:10]]
