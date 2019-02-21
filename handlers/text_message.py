import random
import string

from telegram import Update, Bot

from models.phrase import Phrase


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


def handle_message(bot: Bot, update: Update):
    message = update.message.text
    words = map(normalize, message.split(' '))
    for trigger_words, trigger_fn in MESSAGE_TRIGGERS.items():
        for word in words:
            if word in trigger_words:
                trigger_fn(bot, update)
