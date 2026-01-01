import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext

from tg.handlers import error_handler, handlers
from tg.utils.history import record_message_in_history

TG_TOKEN = os.environ["TG_TOKEN"]

_application: Application | None = None


async def _global_message_recorder(update: Update, context: CallbackContext) -> None:
    if update.effective_message:
        await record_message_in_history(update.effective_message, context)


def get_tg_application() -> Application:
    global _application
    if _application is None:
        _application = Application.builder().token(TG_TOKEN).build()
        # High priority group (-1) to record history before other handlers
        _application.add_handler(
            MessageHandler(filters.ALL, _global_message_recorder), group=-1
        )
        _application.add_handlers(handlers)
        _application.add_error_handler(error_handler)  # type: ignore[invalid-argument-type]

    return _application
