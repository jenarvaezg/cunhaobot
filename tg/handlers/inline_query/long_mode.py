import random
from typing import List
from telegram import InlineQueryResultArticle, InputTextMessageContent

from models.phrase import LongPhrase
from utils import get_thumb


def get_long_mode_results(input: str) -> List[InlineQueryResultArticle]:
    max_results_number = 10
    phrases = LongPhrase.get_phrases(search=input)
    random.shuffle(phrases)
    results_number = min(len(phrases), max_results_number)

    results = [InlineQueryResultArticle(
        id=f"long-{phrase}" if len(phrase) < 50 else f"long-{phrase[:50]}",
        title=phrase,
        input_message_content=InputTextMessageContent(phrase),
        thumb_url=get_thumb()
    ) for phrase in random.sample(phrases, results_number)]

    return results
