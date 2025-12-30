from telegram import Update
from telegram.ext import CallbackContext

from services import user_service, phrase_service
from tg.decorators import log_update


@log_update
async def handle_chosen_inline_result(update: Update, context: CallbackContext):
    if user := user_service.update_or_create_inline_user(update):
        user_service.add_inline_usage(user)

    if not (result := update.chosen_inline_result):
        return

    phrase_service.add_usage_by_id(result.result_id)
