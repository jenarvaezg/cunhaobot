from telegram import Update, Bot


def handle_help(bot: Bot, update: Update):
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        'Puedes usar /submit <frase> para proponer tu frase de cuñado favorita.\n'
        'Tambien puedes invocarme en cualquier chat con @cunhaobot (como el bot de gifs ' 
        'para recibir frases de cuñao.')
