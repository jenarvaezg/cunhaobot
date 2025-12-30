import random
from telegram import InlineQueryResultArticle, InputTextMessageContent
from services import phrase_repo
from utils import get_thumb, normalize_str, random_combination

BASE_TEMPLATE = "¿Qué pasa, {}?"


def _result_id_for_combination(combination: tuple) -> str:
    words = [str(c) for c in combination]
    return f"short-{normalize_str(','.join(words), remove_punctuation=False)}"[:63]


def get_short_mode_results(input_text: str) -> list[InlineQueryResultArticle]:
    if input_text == "":
        size, finisher = 1, ""
    else:
        query_words = input_text.split(" ")
        try:
            size = int(query_words[0])
            finisher = " ".join(query_words[1:])
        except ValueError:
            size = 1
            finisher = input_text

    phrases = phrase_repo.load_all()
    if not phrases:
        return []

    random.shuffle(phrases)
    size = min(size, len(phrases))
    combinations = set()

    for _ in range(10):
        combination = random_combination(phrases, size)
        combinations.add(combination if not finisher else combination + (finisher,))

    results = [
        InlineQueryResultArticle(
            id=_result_id_for_combination(combination),
            title=", ".join([str(e) for e in combination]),
            input_message_content=InputTextMessageContent(
                BASE_TEMPLATE.format(", ".join([str(e) for e in combination]))
            ),
            thumbnail_url=get_thumb(),
        )
        for combination in combinations
    ]

    random.shuffle(results)
    return results
