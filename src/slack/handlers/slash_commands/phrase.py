import random
from typing import Any

from slack.attachments import build_phrase_attachments


def _usage(phrase_service: Any) -> dict:
    random_phrase = phrase_service.get_random().text if phrase_service else "cuñao"
    return {
        "text": "Usando /cuñao <texto> te doy frases de cuñao que incluyan texto en su contenido. Si no me das"
        f"texto para buscar, tendrás una frase al azar, {random_phrase}",
    }


def handle_phrase(slack_data: dict, phrase_service: Any = None) -> dict:
    text = slack_data["text"]
    if text == "help":
        return _usage(phrase_service)

    phrases = (
        phrase_service.get_phrases(search=text, long=True) if phrase_service else []
    )
    if not phrases:
        random_phrase = phrase_service.get_random().text if phrase_service else "cuñao"
        return {
            "indirect": {
                "text": f'No tengo ninguna frase que encaje con la busqueda "{text}", {random_phrase}.'
            },
            "direct": "",
        }

    phrase = random.choice(phrases)
    return {
        "indirect": {"attachments": build_phrase_attachments(phrase.text, search=text)},
        "direct": "",
    }
