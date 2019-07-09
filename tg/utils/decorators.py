import logging
from functools import wraps

from telegram import Update, Bot

from models.schedule import ScheduledTask
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
            if update.effective_message.left_chat_member.username == 'cunhaobot':  # Kicked
                User.load(chat_id=update.effective_message.chat_id).delete()
                [task.delete() for task in ScheduledTask.get_tasks(chat_id=update.effective_message.chat_id)]
        except:
            pass
        update_dict = remove_empty_from_dict(update.to_dict())
        update_dict['method'] = f.__name__

        logger.info(f"{update_dict}")
        return f(bot, update, *args, **kwargs)

    return wrapper
