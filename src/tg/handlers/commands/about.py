from telegram import Update
from telegram.ext import CallbackContext
from tg.decorators import log_update
from services import usage_service, phrase_service
from models.usage import ActionType
from tg.utils.badges import notify_new_badges


@log_update
async def handle_about(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    new_badges = await usage_service.log_usage(
        user_id=message.from_user.id if message.from_user else "unknown",
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "about"},
    )
    await notify_new_badges(update, context, new_badges)

    p = (await phrase_service.get_random()).text
    await message.reply_text(
        f"Este bot ha sido creado por un {p} muy aburrido.\n"
        "Puedes ver el código fuente en GitHub: https://github.com/josesarmiento/cunhaobot",
        do_quote=True,
    )
