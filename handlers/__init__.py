from telegram.ext import InlineQueryHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, \
    ChosenInlineResultHandler

from utils.decorators import log_update
from .about import handle_about
from .callback_query import handle_callback_query
from .error import error_handler
from .help import handle_help
from .inline_query import handle_inline_query
from .start import handle_start
from .submit import handle_submit, handle_submit_long
from .chosen_inine_result import handle_chosen_inline_result
from .text_message import handle_message


@log_update
def handle_fallback_message(bot, update):
    """This is here to handle the rest of messages"""
    pass


handlers = [
    CommandHandler("start", handle_start),
    CommandHandler("help", handle_help),
    CommandHandler('submit', handle_submit),
    CommandHandler('proponer', handle_submit),
    CommandHandler('submitlong', handle_submit_long),
    CommandHandler('proponerfrase', handle_submit_long),
    CommandHandler('about', handle_about),
    MessageHandler(Filters.text, handle_message),
    InlineQueryHandler(handle_inline_query),
    CallbackQueryHandler(handle_callback_query),
    ChosenInlineResultHandler(handle_chosen_inline_result),
    MessageHandler(None, handle_fallback_message),
]
