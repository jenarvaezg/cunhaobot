import random
from typing import Tuple, List
from telegram import InlineQueryResultArticle, InputTextMessageContent

from models.phrase import Phrase
from utils import get_thumb, random_combination, normalize_str


BASE_TEMPLATE = "¿Qué pasa, {}?"


def _result_id_for_combination(combination: Tuple[Phrase]) -> str:
    words = [c.text for c in combination]
    return f"short-{normalize_str(','.join(words), remove_punctuation=False)}"[:63]


def get_short_mode_results(input: str) -> List[InlineQueryResultArticle]:
    if input == "":
        size, finisher = 1, ""
    else:
        query_words = input.split(" ")
        size, finisher = int(query_words[0]), " ".join(query_words[1:])

    phrases = Phrase.get_phrases()
    random.shuffle(phrases)
    size = size if size <= len(phrases) else len(phrases)
    combinations = set()

    for i in range(10):
        combination = random_combination(phrases, size)
        random.shuffle(phrases)
        combinations.add(combination if not finisher else combination + (finisher,))

    results = [
        InlineQueryResultArticle(
            id=_result_id_for_combination(combination),
            title=", ".join([str(e) for e in combination]),
            input_message_content=InputTextMessageContent(
                BASE_TEMPLATE.format(", ".join([str(e) for e in combination]))
            ),
            thumb_url=get_thumb(),
        )
        for combination in combinations
    ]

    random.shuffle(results)

    return results
