import logging

from telegram import Update, TelegramError, Bot

logger = logging.getLogger('cunhaobot')


def error_handler(bot: Bot, update: Update, error: TelegramError):
    """Log Errors caused by Updates."""
    print("ERROR", error, update)
    logger.warning('Update "%s" caused error "%s"', update, error)
