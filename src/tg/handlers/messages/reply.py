from telegram import Update
from telegram.ext import CallbackContext
from models.phrase import Phrase, LongPhrase
from .text_message import handle_message


async def handle_reply(update: Update, context: CallbackContext) -> None:
    if not (msg := update.effective_message) or not msg.reply_to_message:
        return

    # Check if they are replying to a bot message that was a prompt for a proposal
    bot_msg = msg.reply_to_message
    if bot_msg.from_user and bot_msg.from_user.username == context.bot.username:
        bot_text = bot_msg.text or ""

        # Determine if it's a short or long phrase proposal
        if f"¿Qué {Phrase.display_name} quieres proponer" in bot_text:
            from ..commands.submit import submit_handling

            await submit_handling(context.bot, update, is_long=False, text=msg.text)
            return
        elif f"¿Qué {LongPhrase.display_name} quieres proponer" in bot_text:
            from ..commands.submit import submit_handling

            await submit_handling(context.bot, update, is_long=True, text=msg.text)
            return

    # Default to normal message handling
    await handle_message(update, context)
