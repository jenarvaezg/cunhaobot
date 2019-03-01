import logging
from functools import wraps

from telegram import Update, Bot

logger = logging.getLogger('cunhaobot')


def log_update(f):
    @wraps(f)
    def wrapper(bot: Bot, update: Update, **kwargs):
        logger.info(f"{f.__name__}: {update}")
        return f(bot, update, **kwargs)

    return wrapper
