from telegram import Update, Bot


def handle_about(bot: Bot, update: Update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        'Soy un bot hecho por @jenarvaezg, si tienes cualquier duda puedes hablar con él.\nMi principal función es '
        'dar frases de cuñao e intervenir en grupos de vez en cuando, méteme en alguno sin compromiso\n'
        'Tambien puedes usarme en modo inline como el bot de gifs para que te de frases cortas o largas\n'
        'Lo que más me gusta es mandar audios, invocandome escribiendo "@cunhaobot audio" te daré varios\n'
        'También puedes proponer frases, pero tienen que ser aprobadas por mayoría absoluta en un consejo de cuñaos.'
    )
