import logging

from telegram import Update, TelegramError, Bot

logger = logging.getLogger('cunhaobot')


def error_handler(bot: Bot, update: Update, error: TelegramError):
    """Log Errors caused by Updates."""
    logger.error(f'Update "{update}" caused error "{error}')
