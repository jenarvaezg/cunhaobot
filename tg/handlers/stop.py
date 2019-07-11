from telegram import Update, Bot

from models.schedule import ScheduledTask
from models.user import User
from tg.decorators import log_update


@log_update
def handle_stop(bot: Bot, update: Update):
    """Send a message when the command /start is issued."""
    User.update_or_create_from_update().delete()
    n_chapas = [task.delete() for task in ScheduledTask.get_tasks(chat_id=update.effective_chat.id)]

    text = 'Has sido borrado de las listas de notificaciones. ¡Si vuelves a hablarme te volveré a añadir!'
    if n_chapas:
        text += "\nTambién he borrado tus {n_chapas} chapas"
    update.effective_message.reply_text(text, quote=True)
