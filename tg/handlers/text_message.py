import random

from telegram import Update, Message
from telegram.ext import CallbackContext

from models.phrase import Phrase
from tg.decorators import log_update


def reply_cunhao(update: Update, context: CallbackContext):
    n_words = random.choice([3, 4, 5])
    words = ", ".join([Phrase.get_random_phrase().text for _ in range(n_words)])
    msg = "Aquí me tienes, {}.".format(words)
    update.effective_message.reply_text(msg, quote=True)


MESSAGE_TRIGGERS = {
    ('cuñao', 'cuñado', 'cunhao', 'cunhaobot'): reply_cunhao,
}


@log_update
def handle_message(update: Update, context: CallbackContext):
    message: Message = update.effective_message

    used_triggers = []
    msg_text = message.text
    for trigger_words, trigger_fn in MESSAGE_TRIGGERS.items():
        if any(word in msg_text for word in trigger_words) and trigger_fn not in used_triggers:
            trigger_fn(update, context)
            used_triggers.append(trigger_fn)
