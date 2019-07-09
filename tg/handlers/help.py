from telegram import Update, Bot

from tg.decorators import log_update
from models.phrase import Phrase, LongPhrase


@log_update
def handle_help(bot: Bot, update: Update):
    """Send a message when the command /help is issued."""
    update.effective_message.reply_text(
        'Puedes usar /proponer <palabra o frase> para proponer tu palabreja de cuñado favorita. '
        f'Ejemplo: "{Phrase.get_random_phrase()}"\n'
        'Puedes usar /submitlong <frase> para proponer tu frase de cuñado favorita. '
        f'Ejemplo: "{LongPhrase.get_random_phrase()}"\n'
        'Tambien puedes invocarme en cualquier chat escribiendo "@cunhaobot" (como el bot de gifs)'
        'para recibir frases de cuñao.\nPuedes pasarme argumentos como el numero de palabras que encadenar.\n'
        'Como mi creador es un figura, tambien te puedo dar audios si escribes: "@cunhaobot audio"\n'
        'Por ultimo, tengo un servicio de chapas maravilloso, para mas informacion escribe /chapa.')
