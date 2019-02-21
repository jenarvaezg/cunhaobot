from telegram.ext import InlineQueryHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from .start import handle_start
from .help import handle_help
from .inline_query import handle_inline_query
from .error import error_handler
from .submit import handle_submit, handle_submit_long
from .callback_query import handle_callback_query
from .text_message import handle_message
from .about import handle_about

handlers = [
    CommandHandler("start", handle_start),
    CommandHandler("help", handle_help),
    CommandHandler('submit', handle_submit),
    CommandHandler('submitlong', handle_submit_long),
    CommandHandler('about', handle_about),
    MessageHandler(Filters.text, handle_message),
    InlineQueryHandler(handle_inline_query),
    CallbackQueryHandler(handle_callback_query),
]
