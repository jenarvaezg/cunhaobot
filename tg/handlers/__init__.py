from telegram.ext import (
    InlineQueryHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ChosenInlineResultHandler,
)

from .about import handle_about
from .callback_query import handle_callback_query
from .cancel import handle_cancel
from .error import error_handler
from .help import handle_help
from .inline_query import handle_inline_query
from .start import handle_start
from .submit import handle_submit, handle_submit_phrase
from .chosen_inine_result import handle_chosen_inline_result
from .text_message import handle_message
from .stop import handle_stop
from .ping import handle_ping
from .reply import handle_reply
from .chapa import (
    handle_create_chapa,
    handle_delete_chapa,
    handle_delete_chapas,
    handle_list_chapas,
)
from .fallback import handle_fallback_message


handlers = [
    CommandHandler("start", handle_start),
    CommandHandler("help", handle_help),
    CommandHandler("submit", handle_submit),
    CommandHandler("proponer", handle_submit),
    CommandHandler("submitphrase", handle_submit_phrase),
    CommandHandler("proponerfrase", handle_submit_phrase),
    CommandHandler("about", handle_about),
    CommandHandler("stop", handle_stop),
    CommandHandler("cancelar", handle_cancel),
    CommandHandler("chapa", handle_create_chapa),
    CommandHandler("chapas", handle_list_chapas),
    CommandHandler("borrarchapa", handle_delete_chapa),
    CommandHandler("borrarchapas", handle_delete_chapas),
    MessageHandler(filters.REPLY, handle_reply),
    MessageHandler(filters.TEXT, handle_message),
    InlineQueryHandler(handle_inline_query),
    CallbackQueryHandler(handle_callback_query),
    ChosenInlineResultHandler(handle_chosen_inline_result),
    MessageHandler(filters.ALL, handle_fallback_message),
]
