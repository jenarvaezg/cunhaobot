import logging

from telegram.ext import CallbackContext

logger = logging.getLogger("cunhaobot")


async def error_handler(update: object, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.error(f'Update "{update}" caused error "{context.error}')
    if isinstance(context.error, BaseException):
        raise context.error
