from telegram import Update
from telegram.ext import CallbackContext
from tg.decorators import log_update
from services import usage_service, phrase_service
from models.usage import ActionType


@log_update
async def handle_start(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    await usage_service.log_usage(
        user_id=message.from_user.id if message.from_user else "unknown",
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "start"},
    )

    p1 = phrase_service.get_random().text
    p2 = phrase_service.get_random().text
    f1 = phrase_service.get_random(long=True).text

    await update.effective_message.reply_text(
        f"¿Qué pasa, {p1}?\n"
        "Soy @cunhaobot, mi función principal es darte frases de cuñao, perfectas para cualquier ocasión.\n"
        f'Puedes usar /proponer <apelativo> para proponer tu palabreja de cuñado favorita. Ejemplo: "{p2}"\n'
        f'Puedes usar /proponerfrase <frase> para proponer tu frase de cuñado favorita. Ejemplo: "{f1}"\n'
        "También puedes invocarme en cualquier chat con @cunhaobot (como el bot de gifs) para recibir frases de cuñao."
    )
