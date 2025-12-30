import os

from telegram.ext import Application

from tg.handlers import error_handler, handlers

TG_TOKEN = os.environ["TG_TOKEN"]

_application: Application | None = None


def get_tg_application() -> Application:
    global _application
    if _application is None:
        _application = Application.builder().token(TG_TOKEN).build()
        _application.add_handlers(handlers)
        _application.add_error_handler(error_handler)  # type: ignore[invalid-argument-type]

    return _application
