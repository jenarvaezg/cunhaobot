import random

from telegram import Update
from telegram.ext import CallbackContext

from models.phrase import Phrase
from tg.decorators import log_update


async def reply_cunhao(update: Update, context: CallbackContext) -> None:
    if not update.effective_message:
        return
    n_words = random.choice([3, 4, 5])
    words = ", ".join([Phrase.get_random_phrase().text for _ in range(n_words)])
    msg = f"Aquí me tienes, {words}."
    await update.effective_message.reply_text(
        msg, reply_to_message_id=update.effective_message.message_id
    )


MESSAGE_TRIGGERS = {
    ("cuñao", "cuñado", "cunhao", "cunhaobot"): reply_cunhao,
}


@log_update
async def handle_message(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not (msg_text := message.text):
        return

    msg_text_lower = msg_text.lower()
    used_triggers = set()

    for trigger_words, trigger_fn in MESSAGE_TRIGGERS.items():
        if trigger_fn in used_triggers:
            continue

        if any(word in msg_text_lower for word in trigger_words):
            await trigger_fn(update, context)
            used_triggers.add(trigger_fn)
