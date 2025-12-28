from telegram import Update
from telegram.ext import CallbackContext

from models.phrase import LongPhrase, Phrase
from models.user import InlineUser
from tg.decorators import log_update


@log_update
async def handle_chosen_inline_result(update: Update, context: CallbackContext):
    if user := InlineUser.update_or_create_from_update(update):
        user.add_usage()

    if not (result := update.chosen_inline_result):
        return

    if "short-" in result.result_id:
        Phrase.add_usage_by_result_id(result.result_id)
    elif "long-" in result.result_id:
        LongPhrase.add_usage_by_result_id(result.result_id)
