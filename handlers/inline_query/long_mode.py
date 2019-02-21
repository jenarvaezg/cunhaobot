import random
from uuid import uuid4
from typing import List
from telegram import InlineQueryResultArticle, InputTextMessageContent

from models.phrase import LongPhrase
from utils import get_thumb


def get_long_mode_results(input: str) -> List[InlineQueryResultArticle]:
    max_results_number = 10
    phrases = LongPhrase.get_phrases()
    random.shuffle(phrases)
    results_number = max_results_number if max_results_number <= len(phrases) else len(phrases)

    results = [InlineQueryResultArticle(
        id=uuid4(),
        title=phrase,
        input_message_content=InputTextMessageContent(phrase),
        thumb_url=get_thumb()
    ) for phrase in random.sample(phrases, results_number)]

    random.shuffle(results)

    return results
