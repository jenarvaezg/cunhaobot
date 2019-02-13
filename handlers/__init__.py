from telegram.ext import InlineQueryHandler, CommandHandler, CallbackQueryHandler

from .start import handle_start
from .help import handle_help
from .inline_query import handle_inline_query
from .error import error_handler
from .submit import handle_submit
from .callback_query import handle_callback_query

handlers = [
    CommandHandler("start", handle_start),
    CommandHandler("help", handle_help),
    CommandHandler('submit', handle_submit),
    InlineQueryHandler(handle_inline_query),
    CallbackQueryHandler(handle_callback_query),
]
