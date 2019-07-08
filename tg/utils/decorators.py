import logging
from functools import wraps

from telegram import Update, Bot

from models.user import User
from utils import remove_empty_from_dict

logger = logging.getLogger('cunhaobot')


def log_update(f):
    @wraps(f)
    def wrapper(bot: Bot, update: Update, *args, **kwargs):
        try:
            User.from_update(update).save()
        except:
            pass

        try:
            if update.message.left_chat_member.username == 'cunhaobot':
                User.load(chat_id=update.message.chat_id).delete()
        except:
            pass
        update_dict = remove_empty_from_dict(update.to_dict())
        update_dict['method'] = f.__name__

        logger.info(f"{update_dict}")
        return f(bot, update, *args, **kwargs)

    return wrapper
