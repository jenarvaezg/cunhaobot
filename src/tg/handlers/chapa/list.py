from telegram import Update
from telegram.ext import CallbackContext

from services import phrase_service, schedule_repo
from tg.decorators import log_update


@log_update
async def handle_list_chapas(update: Update, context: CallbackContext) -> None:
    if not update.effective_chat or not update.effective_message:
        return

    tasks = schedule_repo.get_schedules(
        chat_id=update.effective_chat.id, task_type="chapa"
    )

    if not tasks:
        p = phrase_service.get_random().text
        await update.effective_message.reply_text(
            f"No hay ninguna chapa configurada en este chat, {p}.", do_quote=True
        )
        return

    text = "Chapas configuradas:\n"
    for task in tasks:
        text += f"- {task.hour:02}:{task.minute:02} (Parámetros: '{task.query}')\n"

    await update.effective_message.reply_text(text, do_quote=True)
