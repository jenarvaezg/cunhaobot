from telegram import Update
from telegram.ext import CallbackContext
from services import phrase_service
from tg.decorators import log_update


@log_update
async def handle_about(update: Update, context: CallbackContext) -> None:
    if not update.effective_message:
        return

    p = phrase_service.get_random().text
    await update.effective_message.reply_text(
        f"Este bot ha sido creado por un {p} muy aburrido.\n"
        "Puedes ver el código fuente en GitHub: https://github.com/josesarmiento/cunhaobot",
        do_quote=True,
    )
