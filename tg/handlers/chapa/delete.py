from telegram import Update, Message, Chat
from telegram.ext import CallbackContext

from models.schedule import ScheduledTask
from tg.decorators import log_update, only_admins
from models.phrase import Phrase


def usage(update: Update) -> Message:
    return update.effective_message.reply_text(
        f"Para borrar chapas, {Phrase.get_random_phrase()}, tienes que escribir /borrachapa X, donde X es el numero de "
        f"la chapa que quieras borrar, {Phrase.get_random_phrase()}\n"
        "Tambien puedes usar /borrarchapas y me lo cargo todo.",
        quote=True
    )


@only_admins
@log_update
def handle_delete_chapas(update: Update, context: CallbackContext):
    chat: Chat = update.effective_chat

    tasks = ScheduledTask.get_tasks(chat_id=chat.id)
    if len(tasks) == 0:
        return update.effective_message.reply_text(
            f"¡Pero si no te estoy dando la chapa, {Phrase.get_random_phrase()}!"
        )

    for task in tasks:
        task.delete()

    update.effective_message.reply_text(
        f"Ya no te daré más chapas, ({len(tasks)} borradas) {Phrase.get_random_phrase()}.",
        quote=True,
    )



@only_admins
@log_update
def handle_delete_chapa(update: Update, context: CallbackContext):
    tokens = update.effective_message.text.split(" ")
    try:
        chapa_id = int(tokens[1]) - 1
    except (IndexError, ValueError) as e:
        return usage(update)

    tasks = ScheduledTask.get_tasks(chat_id=update.effective_chat.id)
    if len(tasks) == 0:
        return update.effective_message.reply_text(
            f"¡Pero si no te estoy dando la chapa, {Phrase.get_random_phrase()}!"
        )

    try:
        task = tasks[chapa_id]
        task.delete()
    except IndexError as e:
        update.effective_message.reply_text(f"Te has pasado con el número, {Phrase.get_random_phrase()}.", quote=True)
    else:
        update.effective_message.reply_text(f"Ya no te daré esa chapa, {Phrase.get_random_phrase()}.", quote=True)


