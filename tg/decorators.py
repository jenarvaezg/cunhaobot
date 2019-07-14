import logging
from functools import wraps

from telegram import Update, Bot, Chat

from models.user import User
from models.phrase import Phrase
from utils import remove_empty_from_dict

logger = logging.getLogger('cunhaobot')


def only_admins(f):
    @wraps(f)
    def wrapper(update: Update, *args, **kwargs):
        chat: Chat = update.effective_chat
        if chat.type == chat.PRIVATE:
            return f(update, *args, **kwargs)
        if chat.all_members_are_administrators:
            return f(update, *args, **kwargs)

        admin_ids = [admin.user.id for admin in chat.get_administrators()]
        if update.effective_user.id in admin_ids:
            return f(update, *args, **kwargs)

        update.effective_message.reply_text(
            f"Esto solo lo pueden hacer administradores, {Phrase.get_random_phrase()}.",
            quote=True,
        )

    return wrapper


def log_update(f):
    @wraps(f)
    def wrapper(update: Update, *args, **kwargs):
        u = User.update_or_create_from_update(update)
        if u:
            u.save()

        update_dict = remove_empty_from_dict(update.to_dict())
        update_dict['method'] = f.__name__

        logger.info(f"{update_dict}")
        return f(update, *args, **kwargs)

    return wrapper
