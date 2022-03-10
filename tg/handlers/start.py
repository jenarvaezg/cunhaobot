from telegram import Update
from telegram.ext import CallbackContext

from models.phrase import Phrase, LongPhrase
from tg.decorators import log_update


@log_update
def handle_start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.effective_message.reply_text(
        f"¿Qué pasa, {Phrase.get_random_phrase()}?\n"
        "Soy CuñaoBot, mi función principal es darte frases de cuñao, perfectas para cualquier ocasión.\n"
        f"Puedes usar /proponer <apelativo> para proponer tu palabreja de cuñado favorita. "
        f'Ejemplo: "{Phrase.get_random_phrase()}"\n'
        "Puedes usar /proponerfrase <frase> para proponer tu frase de cuñado favorita. "
        f'Ejemplo: "{LongPhrase.get_random_phrase()}"\n'
        "Tambien puedes invocarme en cualquier chat con @cunhaobot (como el bot de gifs) para recibir frases de cuñao."
    )
