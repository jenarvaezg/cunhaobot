from telegram.ext import (
    CallbackQueryHandler,
    ChosenInlineResultHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from .commands.about import handle_about
from .utils.callback_query import handle_callback_query
from .commands.cancel import handle_cancel
from .payments.checkout import handle_pre_checkout, handle_successful_payment
from .inline.chosen_inline_result import handle_chosen_inline_result
from .utils.error import error_handler as error_handler
from .messages.fallback import handle_fallback_message as handle_fallback_message
from .commands.help import handle_help as handle_help
from .commands.link import handle_link
from .commands.game import handle_game_command, handle_game_callback, handle_top_jugones
from .commands.poster import handle_poster
from .commands.gift import handle_gift_command, handle_gift_selection
from .commands.profile import handle_profile
from .inline.inline_query import handle_inline_query as handle_inline_query
from .commands.ping import handle_ping as handle_ping
from .messages.reply import handle_reply
from .commands.start import handle_start
from .commands.stop import handle_stop
from .commands.submit import handle_submit, handle_submit_phrase
from .commands.premium import handle_premium
from .messages.text_message import handle_message
from .messages.photo import photo_roast

handlers = [
    CommandHandler("start", handle_start),
    CommandHandler("help", handle_help),
    CommandHandler("premium", handle_premium),
    CommandHandler("regalar", handle_gift_command),
    CommandHandler("gift", handle_gift_command),
    CommandHandler("submit", handle_submit),
    CommandHandler("proponer", handle_submit),
    CommandHandler("submitphrase", handle_submit_phrase),
    CommandHandler("proponerfrase", handle_submit_phrase),
    CommandHandler("profile", handle_profile),
    CommandHandler("perfil", handle_profile),
    CommandHandler("link", handle_link),
    CommandHandler("vincular", handle_link),
    CommandHandler("about", handle_about),
    CommandHandler("stop", handle_stop),
    CommandHandler("cancelar", handle_cancel),
    CommandHandler("jugar", handle_game_command),
    CommandHandler("top_jugones", handle_top_jugones),
    CommandHandler("poster", handle_poster),
    PreCheckoutQueryHandler(handle_pre_checkout),
    MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment),
    MessageHandler(filters.REPLY, handle_reply),
    MessageHandler(filters.PHOTO, photo_roast),
    MessageHandler(filters.TEXT, handle_message),
    InlineQueryHandler(handle_inline_query),
    CallbackQueryHandler(handle_game_callback),
    CallbackQueryHandler(handle_gift_selection, pattern="^gift_sel:"),
    CallbackQueryHandler(handle_callback_query),
    ChosenInlineResultHandler(handle_chosen_inline_result),
    MessageHandler(filters.ALL, handle_fallback_message),
]
