from telegram import Update
from telegram.ext import CallbackContext

from tg.decorators import log_update


@log_update
def handle_about(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.effective_message.reply_text(
        "Soy un bot hecho por @jenarvaezg, si tienes cualquier duda puedes hablar con él.\n"
        "Mis tripas las puedes ver en https://github.com/jenarvaezg/cunhaobot\n "
        "Mi principal función es "
        "dar frases de cuñao e intervenir en grupos de vez en cuando, méteme en alguno sin compromiso\n"
        "Tambien puedes usarme en modo inline como el bot de gifs para que te de saludos frases cuñadiles\n"
        'Lo que más me gusta es mandar audios, invocandome escribiendo "@cunhaobot audio" te daré varios\n'
        "También puedes proponer frases o apelativos, pero tienen que ser aprobadas por mayoría absoluta "
        "en un consejo de cuñaos."
    )
