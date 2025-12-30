from telegram.ext import (
    CallbackQueryHandler,
    ChosenInlineResultHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from .commands.about import handle_about
from .utils.callback_query import handle_callback_query
from .commands.cancel import handle_cancel
from .chapa import (
    handle_create_chapa,
    handle_delete_chapa,
    handle_list_chapas,
)
from .inline.chosen_inine_result import handle_chosen_inline_result
from .utils.error import error_handler as error_handler
from .messages.fallback import handle_fallback_message as handle_fallback_message
from .commands.help import handle_help as handle_help
from .inline.inline_query import handle_inline_query as handle_inline_query
from .commands.ping import handle_ping as handle_ping
from .messages.reply import handle_reply
from .commands.start import handle_start
from .commands.stop import handle_stop
from .commands.submit import handle_submit, handle_submit_phrase
from .messages.text_message import handle_message

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
    CommandHandler("borrarchapas", handle_delete_chapa),  # Apuntar ambos al mismo
    MessageHandler(filters.REPLY, handle_reply),
    MessageHandler(filters.TEXT, handle_message),
    InlineQueryHandler(handle_inline_query),
    CallbackQueryHandler(handle_callback_query),
    ChosenInlineResultHandler(handle_chosen_inline_result),
    MessageHandler(filters.ALL, handle_fallback_message),
]
