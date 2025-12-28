from telegram import Update, Message, Bot
from telegram.ext import CallbackContext

from tg.decorators import log_update
from models.phrase import Phrase, LongPhrase

from . import handle_submit, handle_submit_phrase


@log_update
async def handle_reply(update: Update, context: CallbackContext):
    message: Message = update.effective_message
    reply_to: Message = message.reply_to_message
    bot: Bot = context.bot

    me = await bot.get_me()
    if reply_to.from_user.username != me.username or "dice que deberiamos" in reply_to.text:
        return  # Dont handle

    if Phrase.name in reply_to.text:
        update.effective_message.text = "/proponer " + message.text
        return await handle_submit(update, context)

    if LongPhrase.name in reply_to.text:
        update.effective_message.text = "/proponerfrase " + message.text
        return await handle_submit_phrase(update, context)
