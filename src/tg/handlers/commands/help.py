from telegram import Update
from telegram.ext import CallbackContext
from tg.decorators import log_update
from services import usage_service, phrase_service
from models.usage import ActionType


@log_update
async def handle_help(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    await usage_service.log_usage(
        user_id=message.from_user.id if message.from_user else "unknown",
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "help"},
    )

    p1 = phrase_service.get_random().text
    p2 = phrase_service.get_random().text
    f1 = phrase_service.get_random(long=True).text

    await update.effective_message.reply_text(
        "Puedes usar /proponer <palabra o apelativo> para proponer tu palabreja de cuñado favorita. "
        f'Ejemplo: "{p1}"\n'
        "Puedes usar /proponerfrase <frase> para proponer tu frase de cuñado favorita. "
        f'Ejemplo: "{f1}"\n'
        'También puedes invocarme en cualquier chat escribiendo "@cunhaobot" (como el bot de gifs) '
        "para recibir frases de cuñao.\nPuedes pasarme argumentos como el número de palabras que encadenar.\n"
        f"Como mi creador es un {p2}, también te puedo dar audios "
        'si escribes: "@cunhaobot audio"'
    )
