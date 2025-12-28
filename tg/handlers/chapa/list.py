from telegram import Update
from telegram.ext import CallbackContext

from models.phrase import Phrase
from models.schedule import ScheduledTask
from tg.decorators import log_update


@log_update
async def handle_list_chapas(update: Update, context: CallbackContext):
    tasks = ScheduledTask.get_tasks(chat_id=update.effective_chat.id)
    if len(tasks) == 0:
        return await update.effective_message.reply_text(
            f"No has configurado chapas, {Phrase.get_random_phrase()}, puedes hacerlo con /chapa.",
            do_quote=True,
        )

    tasks_str = "\n".join([f"{pos + 1} -> {task}" for pos, task in enumerate(tasks)])

    await update.effective_message.reply_text(
        f"Estas son las chapas que tienes configuradas, {Phrase.get_random_phrase()}:\n{tasks_str}.",
        do_quote=True,
    )
