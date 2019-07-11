from telegram import Update
from telegram.ext import CallbackContext

from models.user import InlineUser
from tg.decorators import log_update


@log_update
def handle_chosen_inline_result(update: Update, context: CallbackContext):
    InlineUser.update_or_create_from_update(update).add_usage()

