from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext

from tg.decorators import log_update
from models.phrase import Phrase


@log_update
def handle_cancel(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.effective_message.reply_text(
        f"Pues vale, {Phrase.get_random_phrase()}.",
        reply_markup=ReplyKeyboardRemove(selective=True),
        quote=True,
    )
