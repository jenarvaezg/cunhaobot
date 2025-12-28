from telegram import Update
from telegram.ext import CallbackContext

from models.schedule import ScheduledTask
from models.user import User
from tg.decorators import log_update


@log_update
async def handle_stop(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    User.update_or_create_from_update(update).delete()
    n_chapas = [
        task.delete()
        for task in ScheduledTask.get_tasks(chat_id=update.effective_chat.id)
    ]

    text = "Has sido borrado de las listas de notificaciones. ¡Si vuelves a hablarme te volveré a añadir!"
    if n_chapas:
        text += "\nTambién he borrado tus {n_chapas} chapas"
    await update.effective_message.reply_text(text, quote=True)
