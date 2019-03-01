import os

from telegram import Update, Bot, InlineKeyboardMarkup

from constants import LIKE
from markup.keyboards import build_vote_keyboard
from models.phrase import Phrase
from models.proposal import get_proposal_class_by_kind
from utils.decorators import log_update

curators_chat_id = int(os.environ.get("MOD_CHAT_ID", '-1'))


def get_required_votes(bot):
    count = bot.get_chat_members_count(curators_chat_id)
    count -= 1  # ignore bot
    return count // 2 + 1


@log_update
def handle_callback_query(bot: Bot, update: Update):
    data = update.callback_query.data
    vote, proposal_id, kind = data.split(":")
    proposal_class = get_proposal_class_by_kind(kind)

    proposal = proposal_class.load(proposal_id)
    if proposal is None:
        # replying to a message that is not a proposal anymore, most likely erased proposal
        update.callback_query.answer("Esa propuesta ha muerto")
        return

    get_required_votes(bot)

    if update.callback_query.from_user.id in proposal.voted_by:
        # Ignore users who already voted
        update.callback_query.answer(f"Tu ya has votado {Phrase.get_random_phrase()}")
        return

    proposal.add_vote(vote == LIKE, update.callback_query.from_user.id)
    proposal.save()
    update.callback_query.answer(f"Tu voto: {vote} ha sido añadido")

    if proposal.likes >= get_required_votes(bot):
        update.callback_query.edit_message_text(
            f"La propuesta '{proposal.text}' queda formalmente aprobada y añadida a la lista"
        )
        bot.send_message(
            proposal.from_chat_id,
            f"Tu propuesta '{proposal.text}' ha sido aprobada, felicidades, {Phrase.get_random_phrase()}",
            reply_to_message_id=proposal.from_message_id
        )
        proposal.phrase_class.upload_from_proposal(proposal)
        proposal.delete()
    elif proposal.dislikes >= get_required_votes(bot):
        update.callback_query.edit_message_text(
            f"La propuesta '{proposal.text}' queda formalmente rechazada")
        bot.send_message(
            proposal.from_chat_id,
            f"Tu propuesta '{proposal.text}' ha sido rechazada, lo siento {Phrase.get_random_phrase()}",
            reply_to_message_id=proposal.from_message_id
        )
        proposal.delete()
    else:
        text = update.callback_query.message.text
        user = update.callback_query.from_user.username or update.callback_query.first_name
        reply_markup = InlineKeyboardMarkup(build_vote_keyboard(proposal.id, proposal.kind))
        update.callback_query.edit_message_text(f"{text}\n{user}: {vote}", reply_markup=reply_markup)
