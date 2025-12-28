from telegram import Bot, Message, Update
from telegram.ext import CallbackContext

from models.phrase import LongPhrase, Phrase
from models.proposal import LongProposal, Proposal
from tg.decorators import log_update

from ..commands.submit import submit_handling


@log_update
async def handle_reply(update: Update, context: CallbackContext):
    message: Message = update.effective_message
    reply_to: Message = message.reply_to_message
    bot: Bot = context.bot

    me = await bot.get_me()
    if (
        reply_to.from_user.username != me.username
        or "dice que deberiamos" in reply_to.text
    ):
        return  # Dont handle

    if Phrase.name in reply_to.text:
        return await submit_handling(bot, update, Proposal, Phrase, text=message.text)

    if LongPhrase.name in reply_to.text:
        return await submit_handling(
            bot, update, LongProposal, LongPhrase, text=message.text
        )
