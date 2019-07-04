import logging
from functools import wraps

from telegram import Update, Bot

from utils import remove_empty_from_dict

logger = logging.getLogger('cunhaobot')


def log_update(f):
    @wraps(f)
    def wrapper(bot: Bot, update: Update, *args, **kwargs):
        update_dict = remove_empty_from_dict(update.to_dict())
        update_dict['method'] = f.__name__

        logger.info(f"{update_dict}")
        return f(bot, update, *args, **kwargs)

    return wrapper
