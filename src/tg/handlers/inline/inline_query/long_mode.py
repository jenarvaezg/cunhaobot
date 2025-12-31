import random
from telegram import InlineQueryResultArticle, InputTextMessageContent
from services import long_phrase_repo, phrase_service
from utils import get_thumb, normalize_str


def get_long_mode_results(input_text: str) -> list[InlineQueryResultArticle]:
    max_results_number = 10
    phrases = long_phrase_repo.get_phrases(search=input_text)

    # Randomize results
    random.shuffle(phrases)
    results_number = min(len(phrases), max_results_number)

    results = [
        InlineQueryResultArticle(
            id=f"long-{phrase.id}",
            title=phrase.text,
            input_message_content=InputTextMessageContent(phrase.text),
            thumbnail_url=get_thumb(),
        )
        for phrase in random.sample(phrases, results_number)
        if phrase.id is not None
    ]

    if not results:
        result_id = f"long-bad-search-{normalize_str(input_text)}"
        random_phrase = phrase_service.get_random(long=True).text
        results = [
            InlineQueryResultArticle(
                id=result_id[:63],
                title="No hay resultados con esa busqueda, toma una frase al azar",
                input_message_content=InputTextMessageContent(random_phrase),
                thumbnail_url=get_thumb(),
            )
        ]

    return results
