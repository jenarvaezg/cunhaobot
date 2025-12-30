from telegram import Update
from telegram.ext import CallbackContext
from services import user_service, user_repo, phrase_service
from tg.decorators import log_update


@log_update
async def handle_stop(update: Update, context: CallbackContext) -> None:
    if (
        not update.effective_user
        or not update.effective_chat
        or not update.effective_message
    ):
        return

    user = user_repo.load(update.effective_chat.id)
    if user:
        user_service.delete_user(user)

    p = phrase_service.get_random().text
    await update.effective_message.reply_text(
        f"Vale, ya me voy a por tabaco, {p}.", do_quote=True
    )
