from telegram import Update, Bot


def handle_help(bot: Bot, update: Update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        'Puedes usar /submit <palabra o frase> para proponer tu palabreja de cuñado favorita. Ejemplo: "figura"\n'
        'Puedes usar /submitlong <frase> para proponer tu frase de cuñado favorita. Ejemplo: "Esto con carmena no pasaba"\n'
        'Tambien puedes invocarme en cualquier chat escribiendo "@cunhaobot" (como el bot de gifs)'
        'para recibir frases de cuñao.\nPuedes pasarme argumentos como el numero de palabras que encadenar.\n'
        'Como mi creador es un figura, tambien te puedo dar audios si escribes: "@cunhaobot audio"')
