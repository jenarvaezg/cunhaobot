import logging
from telegram import (
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
    Update,
)
from telegram.ext import CallbackContext

from services import phrase_service, user_service
from tg.decorators import log_update
from tg.handlers.inline.inline_query.sticker_mode import get_sticker_mode_results
from tg.text_router import (
    AUDIO_MODE,
    LONG_MODE,
    SHORT_MODE,
    STICKER_MODE,
    get_query_mode,
)
from utils import get_thumb, normalize_str

from .audio_mode import get_audio_mode_results
from .long_mode import get_long_mode_results
from .short_mode import get_short_mode_results

logger = logging.getLogger("cunhaobot")

MODE_HANDLERS = {
    SHORT_MODE: get_short_mode_results,
    LONG_MODE: get_long_mode_results,
    AUDIO_MODE: get_audio_mode_results,
    STICKER_MODE: get_sticker_mode_results,
}


@log_update
async def handle_inline_query(update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    if not update.inline_query:
        return

    mode, rest = get_query_mode(update.inline_query.query)

    results_func = MODE_HANDLERS.get(mode)
    if not results_func:
        p = (await phrase_service.get_random()).text
        await update.inline_query.answer(
            [
                InlineQueryResultArticle(
                    id="Dont know how to use",
                    title="No sabes usarme :(, hablame por privado y escribe /help",
                    input_message_content=InputTextMessageContent(
                        f"Soy un {p} y no se usar el CuñaoBot"
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

    results = await results_func(rest)

    switch_pm_param = f"{mode}-{normalize_str(rest.replace(' ', '-'))}"
    await update.inline_query.answer(
        results,
        cache_time=1,
        button=InlineQueryResultsButton(
            text="PULSA AQUÍ PARA RECIBIR AYUDA",
            start_parameter=switch_pm_param[:63],
        ),
    )

    await user_service.update_or_create_inline_user(update)
