from telegram import Update, Bot

from models.phrase import Phrase
from utils.decorators import log_update


@log_update
def handle_start(bot: Bot, update: Update):
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        f'¿Que pasa, {Phrase.get_random_phrase()}? '
        'Soy CuñaoBot, mi función principal es darte frases de cuñao, perfectas para cualquier ocasión.\n'
        'Puedes usar /submit <palabra o frase> para proponer tu palabreja de cuñado favorita. Ejemplo: "figura"\n'
        'Puedes usar /submitlong <frase> para proponer tu frase de cuñado favorita. Ejemplo: "Esto con carmena no pasaba"\n'
        'Tambien puedes invocarme en cualquier chat con @cunhaobot (como el bot de gifs) para recibir frases de cuñao'
    )
