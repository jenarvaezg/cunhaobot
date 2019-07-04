from typing import List

from telegram import Update, Bot, Message

from models.schedule import ScheduledTask
from tg.utils.decorators import log_update
from models.phrase import Phrase


def usage(update: Update) -> Message:
    return update.message.reply_text(
        f"Para borrar chapas, {Phrase.get_random_phrase()}, tienes que escribir /borrachapa X, donde X es el numero de "
        f"la chapa que quieras borrar, {Phrase.get_random_phrase()}\n"
        "Tambien puedes usar /borrarchapas y me lo cargo todo",
        quote=True
    )


def delete_all_chapas(tasks: List[ScheduledTask], update: Update):
    for task in tasks:
        task.delete()
    update.message.reply_text(f"Ya no te daré más {len(tasks)} chapas, {Phrase.get_random_phrase()}", quote=True)


def delete_one_chapa(tasks: List[ScheduledTask], chapa_id: int, update: Update):
    try:
        task = tasks[chapa_id]
        task.delete()
    except IndexError as e:
        update.message.reply_text(f"Te has pasado con el número, {Phrase.get_random_phrase()}", quote=True)
    else:
        update.message.reply_text(f"Ya no te daré esa chapa, {Phrase.get_random_phrase()}", quote=True)


@log_update
def handle_delete_chapa(bot: Bot, update: Update):
    tokens = update.message.text.split(" ")
    try:
        cmd = tokens[0]
        if cmd.endswith('s'):
            chapa_id = None
        else:
            chapa_id = int(tokens[1]) - 1
    except (IndexError, ValueError) as e:
        return usage(update)

    tasks = ScheduledTask.get_tasks(chat_id=update.effective_chat.id)
    if len(tasks) == 0:
        return update.message.reply_text(f"¡Pero si no te estoy dando la chapa, {Phrase.get_random_phrase()}!")
    if chapa_id is None:
        delete_all_chapas(tasks, update)
    else:
        delete_one_chapa(tasks, chapa_id, update)


