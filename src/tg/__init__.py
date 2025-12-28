import os

from telegram.ext import Application

from tg.handlers import error_handler, handlers

TG_TOKEN = os.environ["TG_TOKEN"]


def get_tg_application() -> Application:
    application = Application.builder().token(TG_TOKEN).build()
    application.add_handlers(handlers)
    application.add_error_handler(error_handler)  # type: ignore[invalid-argument-type]

    return application
