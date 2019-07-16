import random

from models.phrase import LongPhrase, Phrase
from slack.attachments import build_phrase_attachments


def _usage() -> dict:
    return {
        'text': 'Usando /cuñao <texto> te doy frases de cuñao que incluyan texto en su contenido. Si no me das'
                f'texto para buscar, tendrás una frase al azar, {Phrase.get_random_phrase()}',
    }


def handle_phrase(slack_data: dict) -> dict:
    text = slack_data['text']
    if text == 'help':
        return _usage()

    phrase = random.choice(LongPhrase.get_phrases(search=text))
    if not phrase:
        return {
            'indirect': {
                'text': f'No tengo ninguna frase que encaje con la busqueda "{text}", {Phrase.get_random_phrase()}'
            },
            'direct': '',
        }

    return {
        'indirect': {
            'attachments': build_phrase_attachments(phrase.text, search=text)
        },
        'direct': '',
    }

