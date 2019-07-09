import random

from telegram import Bot, Update, Message

from tg.decorators import log_update

from models.phrase import Phrase
from models.user import User
from models.schedule import ScheduledTask


def _on_kick(chat_id: int) -> None:
    User.load(chat_id=chat_id).delete()
    [task.delete() for task in ScheduledTask.get_tasks(chat_id=chat_id)]


def _on_other_kicked(bot: Bot, user: User, chat_id: int) -> None:
    bot.send_message(
        chat_id,
        f"Vaya {Phrase.get_random_phrase()} el {user.name}, ya me jodería."
    )


def _on_join(bot: Bot, chat_id: int) -> None:
    bot.send_message(
        chat_id,
        "¡Muchas gracias por meterme en el grupo! Te recomiendo usar /help para explicarte que puedo hacer, "
        f"{Phrase.get_random_phrase()}."
    )


def _on_other_joined(bot: Bot, user: User, chat_id: int) -> None:
    n_words = random.choice([2, 3, 4])
    phrases = [user.name] + [Phrase.get_random_phrase() for _ in range(n_words)]
    words = ", ".join(phrases)
    bot.send_message(
        chat_id,
        f'¿Qué pasa, {words}?'
    )


@log_update
def handle_fallback_message(bot: Bot, update: Update):
    """This is here to handle the rest of messages, mainly service messages"""
    message: Message = update.effective_message

    my_username = bot.get_me().username
    if message.left_chat_member:
        if message.left_chat_member.username == my_username:
            return _on_kick(message.chat_id)
        else:
            return _on_other_kicked(bot, message.left_chat_member, message.chat_id)

    if message.new_chat_members:
        for user in message.new_chat_members:
            if user.username == my_username:
                _on_join(bot, message.chat_id)
            else:
                _on_other_joined(bot, user, message.chat_id)
