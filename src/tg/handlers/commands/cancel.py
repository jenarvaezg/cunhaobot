from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext

from models.phrase import Phrase
from tg.decorators import log_update


@log_update
async def handle_cancel(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    if not update.effective_message:
        return
    await update.effective_message.reply_text(
        f"Pues vale, {Phrase.get_random_phrase()}.",
        reply_markup=ReplyKeyboardRemove(selective=True),
        do_quote=True,
    )
