import os

from telegram.ext import Updater, Dispatcher

from tg.handlers import error_handler, handlers

TG_TOKEN = os.environ["TG_TOKEN"]


def tg_dispatcher() -> Dispatcher:
    # Create the Updater and pass it your bot's token.
    updater = Updater(TG_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    for handler in handlers:
        dp.add_handler(handler)

    # log all errors
    dp.add_error_handler(error_handler)

    return dp
