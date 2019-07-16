import random
from typing import List
from telegram import InlineQueryResultArticle, InputTextMessageContent

from models.phrase import LongPhrase
from utils import get_thumb, normalize_str


def get_long_mode_results(input: str) -> List[InlineQueryResultArticle]:
    max_results_number = 10
    phrases = LongPhrase.get_phrases(search=input)
    random.shuffle(phrases)
    results_number = min(len(phrases), max_results_number)

    results = [InlineQueryResultArticle(
        id=f"long-{normalize_str(phrase.text)[:58]}",
        title=phrase.text,
        input_message_content=InputTextMessageContent(phrase.text),
        thumb_url=get_thumb()
    ) for phrase in random.sample(phrases, results_number)]

    if not results:
        result_id = f'long-bad-search-{normalize_str(input)}'
        results = [InlineQueryResultArticle(
            id=result_id[:63],
            title='No hay resultados con esa busqueda, toma una frase al azar',
            input_message_content=InputTextMessageContent(LongPhrase.get_random_phrase().text),
            thumb_url=get_thumb()
        )]

    return results
