from telegram import Update
from telegram.ext import CallbackContext

from models.phrase import LongPhrase, Phrase
from tg.decorators import log_update


@log_update
async def handle_start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    if not update.effective_message:
        return
    await update.effective_message.reply_text(
        f"¿Qué pasa, {Phrase.get_random_phrase()}?\n"
        f"Soy , mi función principal es darte frases de cuñao, perfectas para cualquier ocasión.\n"
        f"Puedes usar /proponer <apelativo> para proponer tu palabreja de cuñado favorita. "
        f'Ejemplo: "{Phrase.get_random_phrase()}"\n'
        "Puedes usar /proponerfrase <frase> para proponer tu frase de cuñado favorita. "
        f'Ejemplo: "{LongPhrase.get_random_phrase()}"\n'
        "Tambien puedes invocarme en cualquier chat con @cunhaobot (como el bot de gifs) para recibir frases de cuñao."
    )
