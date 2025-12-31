import random
from telegram import InlineQueryResultArticle, InputTextMessageContent
from services import phrase_repo
from utils import get_thumb, normalize_str, random_combination

BASE_TEMPLATE = "¿Qué pasa, {}?"


def _result_id_for_combination(combination: tuple) -> str:
    parts = []
    for c in combination:
        if hasattr(c, "id") and c.id is not None:
            parts.append(str(c.id))

    if not parts:
        # Fallback or empty combination? Should not happen if data is correct
        return "short-invalid"

    safe_id = ",".join(parts)
    return f"short-{safe_id}"[:63]


def get_short_mode_results(input_text: str) -> list[InlineQueryResultArticle]:
    input_text = input_text.strip()
    if input_text == "":
        size, search = 1, ""
    else:
        query_words = input_text.split(" ")
        try:
            size = int(query_words[0])
            search = " ".join(query_words[1:])
        except ValueError:
            size = 1
            search = input_text

    phrases = phrase_repo.load_all()
    if not phrases:
        return []

    if search:
        search_norm = normalize_str(search)
        matching = [p for p in phrases if search_norm in normalize_str(p.text)]
        if matching:
            phrases = matching
        else:
            return [
                InlineQueryResultArticle(
                    id=f"short-no-results-{search_norm}"[:63],
                    title=f'No tengo ningún saludo con "{search}"',
                    input_message_content=InputTextMessageContent(
                        f"He intentado saludar como un cuñao usando {search} pero no me sale nada."
                    ),
                    thumbnail_url=get_thumb(),
                )
            ]

    # Randomize
    phrases_to_sample = list(phrases)
    random.shuffle(phrases_to_sample)

    size = max(1, min(size, len(phrases_to_sample)))
    combinations = set()

    # Try to get 10 different combinations
    for _ in range(20):
        if len(combinations) >= 10:
            break
        combination = random_combination(phrases_to_sample, size)
        combinations.add(combination)

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
