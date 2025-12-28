from telegram import Update, Bot
from telegram.ext import CallbackContext

from tg.decorators import log_update
from models.phrase import Phrase, LongPhrase


@log_update
async def handle_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    await update.effective_message.reply_text(
        "Puedes usar /proponer <palabra o apelativo> para proponer tu palabreja de cuñado favorita. "
        f'Ejemplo: "{Phrase.get_random_phrase()}"\n'
        "Puedes usar /proponerfrase <frase> para proponer tu frase de cuñado favorita. "
        f'Ejemplo: "{LongPhrase.get_random_phrase()}"\n'
        'Tambien puedes invocarme en cualquier chat escribiendo "@cunhaobot" (como el bot de gifs)'
        "para recibir frases de cuñao.\nPuedes pasarme argumentos como el numero de palabras que encadenar.\n"
        f"Como mi creador es un {Phrase.get_random_phrase()}, tambien te puedo dar audios "
        'si escribes: "@cunhaobot audio"\n'
        "Por ultimo, tengo un servicio de chapas maravilloso, para mas informacion escribe /chapa."
    )
