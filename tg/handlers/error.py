import logging

from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger('cunhaobot')


def error_handler(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.error(f'Update "{update}" caused error "{context.error}')
