from telegram import Update
from telegram.ext import CallbackContext

from models.schedule import ScheduledTask
from models.user import User
from tg.decorators import log_update


@log_update
async def handle_stop(update: Update, context: CallbackContext):
    if (
        not update.effective_user
        or not update.effective_chat
        or not update.effective_message
    ):
        return

    user = User.load(update.effective_chat.id)
    if user:
        user.delete()
    tasks = ScheduledTask.get_tasks(chat_id=update.effective_chat.id)
    n_chapas = len(tasks)
    for task in tasks:
        task.delete()

    text = "Has sido borrado de las listas de notificaciones. ¡Si vuelves a hablarme te volveré a añadir!"
    if n_chapas:
        text += f"\nTambién he borrado tus {n_chapas} chapas"
    await update.effective_message.reply_text(text, do_quote=True)
