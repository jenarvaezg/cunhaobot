import random


from telegram import InlineQueryResultCachedSticker

from models.phrase import LongPhrase, Phrase
from core.container import services
from tg.text_router import LONG_MODE, SHORT_MODE, get_query_mode


def _phrase_to_inline_sticker(
    phrase: Phrase | LongPhrase, result_type: str
) -> InlineQueryResultCachedSticker | None:
    if phrase.id is None:
        return None

    result_id = f"sticker-{result_type}-{phrase.id}"
    return InlineQueryResultCachedSticker(
        id=result_id[:63], sticker_file_id=phrase.sticker_file_id
    )


async def get_sticker_mode_results(input: str) -> list[InlineQueryResultCachedSticker]:
    mode, rest = get_query_mode(input)

    phrases: list[Phrase | LongPhrase] = []
    result_type = ""
    if mode == SHORT_MODE:
        result_type = "short"
        phrases.extend(await services.phrase_repo.get_phrases(search=rest))
    elif mode == LONG_MODE:
        result_type = "long"
        phrases.extend(await services.long_phrase_repo.get_phrases(search=rest))

    random.shuffle(phrases)
    results: list[InlineQueryResultCachedSticker] = []
    for p in phrases[:10]:
        if res := _phrase_to_inline_sticker(p, result_type):
            results.append(res)
    return results
