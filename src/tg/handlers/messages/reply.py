from telegram import Bot, Update
from telegram.ext import CallbackContext

from models.phrase import LongPhrase, Phrase
from models.proposal import LongProposal, Proposal
from tg.decorators import log_update

from ..commands.submit import submit_handling


@log_update
async def handle_reply(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not (
        reply_to := message.reply_to_message
    ):
        return

    bot: Bot = context.bot
    me = await bot.get_me()

    if not reply_to.from_user or reply_to.from_user.username != me.username:
        return

    if not reply_to.text or "dice que deberiamos" in reply_to.text:
        return

    match reply_to.text:
        case t if Phrase.name in t:
            await submit_handling(bot, update, Proposal, Phrase, text=message.text)
        case t if LongPhrase.name in t:
            await submit_handling(
                bot, update, LongProposal, LongPhrase, text=message.text
            )
