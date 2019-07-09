from telegram import Update, Bot

from models.schedule import ScheduledTask
from tg.utils.decorators import log_update
from models.phrase import Phrase


@log_update
def handle_list_chapas(bot: Bot, update: Update):
    tasks = ScheduledTask.get_tasks(chat_id=update.effective_chat.id)
    if len(tasks) == 0:
        return update.effective_message.reply_text(
            f"No has configurado chapas, {Phrase.get_random_phrase()}, puedes hacerlo con /chapa.",
            quote=True
        )

    tasks_str = "\n".join([f"{pos+1} -> {task}" for pos, task in enumerate(tasks)])

    update.effective_message.reply_text(
        f"Estas son las chapas que tienes configuradas, {Phrase.get_random_phrase()}:\n{tasks_str}.",
        quote=True
    )
