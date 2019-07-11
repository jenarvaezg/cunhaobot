import logging
from typing import Tuple

from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram import Update, Bot

from models.user import InlineUser
from utils import get_thumb
from models.phrase import Phrase
from tg.decorators import log_update

from .short_mode import get_short_mode_results
from .audio_mode import get_audio_mode_results
from .long_mode import get_long_mode_results

logger = logging.getLogger('cunhaobot')
SHORT_MODE_WORDS = ['short', 'corto', 'corta', 'saludo']
LONG_MODE_WORDS = ['long', 'largo', 'larga', 'frase']
AUDIO_MODE_WORDS = ['audio', 'sonido', 'sound']
SHORT_MODE = 'SHORT'
LONG_MODE = 'LONG'
AUDIO_MODE = 'AUDIO'


MODE_HANDLERS = {
    SHORT_MODE: get_short_mode_results,
    LONG_MODE: get_long_mode_results,
    AUDIO_MODE: get_audio_mode_results,
}


def get_query_mode(query: str) -> Tuple[str, str]:
    clean_query = query.strip()
    query_words = clean_query.split(' ')
    if clean_query == '' or query_words[0] in SHORT_MODE_WORDS:
        return SHORT_MODE, ' '.join(query_words[1:])

    if query_words[0].isnumeric():
        return SHORT_MODE, ' '.join(query_words)

    if query_words[0] in AUDIO_MODE_WORDS:
        return AUDIO_MODE, ' '.join(query_words[1:])

    if query_words[0] in LONG_MODE_WORDS:
        return LONG_MODE, ' '.join(query_words[1:])

    if query_words[0].isalpha():
        return LONG_MODE, ' '.join(query_words[0:])

    logging.error(f"Somehow user reached this point, dont know how to use: {query}")
    return '', ''


@log_update
def handle_inline_query(bot: Bot, update: Update):
    """Handle the inline query."""
    mode, rest = get_query_mode(update.inline_query.query)

    results_func = MODE_HANDLERS.get(mode)
    if not results_func:
        update.inline_query.answer([
            InlineQueryResultArticle(
                id='Dont know how to use',
                title='No sabes usarme :(, hablame por privado y escribe /help',
                input_message_content=InputTextMessageContent(
                    f'Soy un {Phrase.get_random_phrase()} y no se usar el CuñaoBot'
                ),
                thumb_url=get_thumb()
            )
        ], switch_pm_text='PULSA AQUI PARA RECIBIR AYUDA', switch_pm_parameter='dont_know_how_to_use')
        return

    results = results_func(rest)

    update.inline_query.answer(
        results,
        cache_time=1,
        switch_pm_text='PULSA AQUÍ PARA RECIBIR AYUDA',
        switch_pm_parameter=f'{mode}-{rest.replace(" ", "-")}'
    )

    InlineUser.update_or_create_from_update(update)
