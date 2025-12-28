import logging
from typing import Tuple

from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultsButton
from telegram import Update
from telegram.ext import CallbackContext

from models.user import InlineUser
from tg.handlers.inline_query.sticker_mode import get_sticker_mode_results
from utils import get_thumb, normalize_str
from models.phrase import Phrase
from tg.decorators import log_update
from tg.text_router import (
    SHORT_MODE,
    LONG_MODE,
    AUDIO_MODE,
    STICKER_MODE,
    get_query_mode,
)

from .short_mode import get_short_mode_results
from .audio_mode import get_audio_mode_results
from .long_mode import get_long_mode_results

logger = logging.getLogger("cunhaobot")

MODE_HANDLERS = {
    SHORT_MODE: get_short_mode_results,
    LONG_MODE: get_long_mode_results,
    AUDIO_MODE: get_audio_mode_results,
    STICKER_MODE: get_sticker_mode_results,
}


@log_update
async def handle_inline_query(update: Update, context: CallbackContext):
    """Handle the inline query."""
    mode, rest = get_query_mode(update.inline_query.query)

    results_func = MODE_HANDLERS.get(mode)
    if not results_func:
        await update.inline_query.answer(
            [
                InlineQueryResultArticle(
                    id="Dont know how to use",
                    title="No sabes usarme :(, hablame por privado y escribe /help",
                    input_message_content=InputTextMessageContent(
                        f"Soy un {Phrase.get_random_phrase()} y no se usar el CuñaoBot"
                    ),
                    thumbnail_url=get_thumb(),
                )
            ],
            button=InlineQueryResultsButton(
                text="PULSA AQUI PARA RECIBIR AYUDA",
                start_parameter="dont_know_how_to_use",
            ),
        )
        return

    results = results_func(rest)

    switch_pm_param = f'{mode}-{normalize_str(rest.replace(" ", "-"))}'
    await update.inline_query.answer(
        results,
        cache_time=1,
        button=InlineQueryResultsButton(
            text="PULSA AQUÍ PARA RECIBIR AYUDA",
            start_parameter=switch_pm_param[:63],
        ),
    )

    InlineUser.update_or_create_from_update(update)
