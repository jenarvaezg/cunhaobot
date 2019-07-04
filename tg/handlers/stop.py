from telegram import Update, Bot

from models.user import User
from tg.utils.decorators import log_update


@log_update
def handle_stop(bot: Bot, update: Update):
    """Send a message when the command /start is issued."""
    User.from_update(update).delete()
    update.message.reply_text(
        'Has sido borrado de las listas de notificaciones, si vuelves a hablarme de volvere a añadir!'
    )
