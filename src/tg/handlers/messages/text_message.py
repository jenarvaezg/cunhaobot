import random
from telegram import Update
from telegram.ext import CallbackContext
from services import phrase_service
from tg.decorators import log_update


@log_update
async def handle_message(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.text:
        return

    text = message.text.lower()
    triggers = ["cuñao", "cuñado", "cuñadismo"]

    if any(t in text for t in triggers):
        # Respond with a random long phrase
        p = phrase_service.get_random(long=True).text
        await message.reply_text(p, do_quote=True)
    elif random.random() < 0.05:  # 5% chance of random interaction
        p = phrase_service.get_random().text
        await message.reply_text(f"¿Qué dices, {p}?", do_quote=True)
