import logging
from typing import Tuple
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram import Update, Bot

from handlers.inline_query.short_mode import get_short_mode_results
from handlers.inline_query.audio_mode import get_audio_mode_results
from utils import get_thumb
from models.phrase import Phrase


logger = logging.getLogger('cunhaobot')
SHORT_MODE_WORDS = ['short', 'corto', 'corta', 'saludo']
LONG_MODE_WORDS = ['long', 'largo', 'larga', 'frase']
AUDIO_MODE_WORDS = ['audio', 'sonido', 'sound', 'mp3', 'ogg']
SHORT_MODE = 'SHORT'
LONG_MODE = 'LONG'
AUDIO_MODE = 'AUDIO'


MODE_HANDLERS = {
    SHORT_MODE: get_short_mode_results,
    AUDIO_MODE: get_audio_mode_results
}


def get_query_mode(query: str) -> Tuple[str, str]:
    clean_query = query.strip()
    query_words = clean_query.split(' ')
    if clean_query == '' or query_words[0] in SHORT_MODE_WORDS:
        return SHORT_MODE, ' '.join(query_words[1:])

    if query_words[0].isnumeric():
        return SHORT_MODE, ' '.join(query_words)

    if query_words[0] in LONG_MODE_WORDS:
        return LONG_MODE, ' '.join(query_words[1:])

    if query_words[0] in AUDIO_MODE_WORDS:
        return AUDIO_MODE, ' '.join(query_words[1:])

    return '', ''


def handle_inline_query(bot: Bot, update: Update):
    """Handle the inline query."""
    mode, rest = get_query_mode(update.inline_query.query)

    results_func = MODE_HANDLERS.get(mode)
    if not results_func:
        update.inline_query.answer([
            InlineQueryResultArticle(
                id=uuid4(),
                title='No sabes usarme :(, hablame por privado y escribe /help',
                input_message_content=InputTextMessageContent(
                    f'Soy un {Phrase.get_random_phrase()} y no se usar el CuñaoBot'
                ),
                thumb_url=get_thumb()
            )
        ])
        return

    results = results_func(rest)
    update.inline_query.answer(results, cache_time=1)
