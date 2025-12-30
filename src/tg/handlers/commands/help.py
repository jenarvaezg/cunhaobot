from telegram import Update
from telegram.ext import CallbackContext
from services import phrase_service
from tg.decorators import log_update


@log_update
async def handle_help(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    if not update.effective_message:
        return

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
