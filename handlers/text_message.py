import random
import string

from telegram import Update, Bot

from models.phrase import Phrase
from models.user import User
from utils.decorators import log_update


def reply_cunhao(bot: Bot, update: Update):
    n_words = random.choice([3, 4, 5])
    words = ", ".join([Phrase.get_random_phrase() for _ in range(n_words)])
    msg = "Aqui me tienes, {}.".format(words)
    update.message.reply_text(msg)


MESSAGE_TRIGGERS = {
    ('cuñao', 'cuñado', 'cunhao', 'cunhaobot', '@cunhaobot'): reply_cunhao,
}

translator = str.maketrans('', '', string.punctuation)


def normalize(word):
    return word.translate(translator).lower()


@log_update
def handle_message(bot: Bot, update: Update):
    if not update.message:
        return
    User.from_update(update).save()
    used_triggers = []
    message = update.message.text
    words = map(normalize, message.split(' '))
    for word in words:
        for trigger_words, trigger_fn in MESSAGE_TRIGGERS.items():
            if word in trigger_words and trigger_fn not in used_triggers:
                trigger_fn(bot, update)
                used_triggers.append(trigger_fn)
