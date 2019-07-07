import random
from uuid import uuid4
from typing import List
from telegram import InlineQueryResultArticle, InputTextMessageContent

from models.phrase import Phrase
from utils import get_thumb, random_combination


BASE_TEMPLATE = '¿Qué pasa, {}?'


def get_short_mode_results(input: str) -> List[InlineQueryResultArticle]:
    if input == '':
        size, finisher = 1, ''
    else:
        query_words = input.split(' ')
        size, finisher = int(query_words[0]), ' '.join(query_words[1:])

    phrases = Phrase.get_phrases()
    random.shuffle(phrases)
    size = size if size <= len(phrases) else len(phrases)
    combinations = set()

    for i in range(10):
        combination = random_combination(phrases, size)
        random.shuffle(phrases)
        combinations.add(combination if not finisher else combination + (finisher,))

    results = [InlineQueryResultArticle(
        id=f"short-{', '.join(combination)}" if len(', '.join(combination)) < 55 else f"short-{', '.join(combination)[:55]}",
        title=', '.join(combination),
        input_message_content=InputTextMessageContent(
            BASE_TEMPLATE.format(', '.join(combination))
        ),
        thumb_url=get_thumb()
    ) for combination in combinations]

    random.shuffle(results)

    return results
