from telegram import Update, ChosenInlineResult
from telegram.ext import CallbackContext

from models.phrase import Phrase, LongPhrase
from models.user import InlineUser
from tg.decorators import log_update


@log_update
async def handle_chosen_inline_result(update: Update, context: CallbackContext):
    InlineUser.update_or_create_from_update(update).add_usage()
    result: ChosenInlineResult = update.chosen_inline_result
    if "short-" in result.result_id:
        Phrase.add_usage_by_result_id(result.result_id)
    elif "long-" in result.result_id:
        LongPhrase.add_usage_by_result_id(result.result_id)
