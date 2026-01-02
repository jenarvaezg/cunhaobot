from telegram import Update
from telegram.ext import CallbackContext

from services import user_service, phrase_service, usage_service
from models.usage import ActionType
from tg.decorators import log_update


@log_update
async def handle_chosen_inline_result(update: Update, context: CallbackContext):
    if user := user_service.update_or_create_inline_user(update):
        user_service.add_inline_usage(user)

    if not (result := update.chosen_inline_result):
        return

    phrase_service.add_usage_by_id(result.result_id)

    # Log usage
    is_sticker = result.result_id.startswith("sticker-")
    is_audio = result.result_id.startswith("audio-")

    if is_sticker:
        action = ActionType.STICKER
    elif is_audio:
        action = ActionType.AUDIO
    else:
        action = ActionType.PHRASE

    new_badges = await usage_service.log_usage(
        user_id=result.from_user.id,
        platform="telegram",
        action=action,
        metadata={"result_id": result.result_id},
    )

    if new_badges:
        from tg.utils.badges import notify_new_badges

        # In inline mode, we notify the user via PRIVATE message
        # We need to ensure we can send messages to them (they must have started the bot)
        await notify_new_badges(update, context, new_badges)
