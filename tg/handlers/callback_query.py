import os
from typing import Any

from telegram import (
    Bot,
    CallbackQuery,
    InlineKeyboardMarkup,
    Update,
    constants,
)
from telegram.ext import CallbackContext

from models.phrase import Phrase
from models.proposal import Proposal, get_proposal_class_by_kind
from tg.constants import LIKE
from tg.decorators import log_update
from tg.markup.keyboards import build_vote_keyboard

curators_chat_id = int(os.environ.get("MOD_CHAT_ID", "-1"))
admins: list[Any] = []  # Cool global var to cache stuff


def get_required_votes():
    count = len(admins)
    return count // 2 + 1


def get_vote_summary(proposal: Proposal) -> str:
    likers = [a.user.name for a in admins if a.user.id in proposal.liked_by]
    dislikers = [a.user.name for a in admins if a.user.id in proposal.disliked_by]
    return f"Han votado que si: {' '.join(likers)}\nHan votado que no: {' '.join(dislikers)}"


async def _add_vote(
    proposal: Proposal, vote: str, callback_query: CallbackQuery
) -> None:
    proposal.add_vote(vote == LIKE, callback_query.from_user.id)
    proposal.save()
    await callback_query.answer(f"Tu voto: {vote} ha sido añadido.")


async def _approve_proposal(
    proposal: Proposal, callback_query: CallbackQuery, bot: Bot
) -> None:
    await callback_query.edit_message_text(
        f"La propuesta '{proposal.text}' queda formalmente aprobada y añadida a la lista.\n\n"
        f"{get_vote_summary(proposal)}",
        disable_web_page_preview=True,
    )
    await bot.send_message(
        proposal.from_chat_id,
        f"Tu propuesta '{proposal.text}' ha sido aprobada, felicidades, {Phrase.get_random_phrase()}",
        reply_to_message_id=proposal.from_message_id,
    )
    await proposal.phrase_class.upload_from_proposal(proposal, bot)


async def _dismiss_proposal(
    proposal: Proposal, callback_query: CallbackQuery, bot: Bot
) -> None:
    await callback_query.edit_message_text(
        f"La propuesta '{proposal.text}' queda formalmente rechazada.\n\n{get_vote_summary(proposal)}",
        disable_web_page_preview=True,
    )

    await bot.send_message(
        proposal.from_chat_id,
        f"Tu propuesta '{proposal.text}' ha sido rechazada, lo siento {Phrase.get_random_phrase()}",
        reply_to_message_id=proposal.from_message_id,
    )
    proposal.delete()


async def _update_proposal_text(
    proposal: Proposal, callback_query: CallbackQuery
) -> None:
    text = callback_query.message.text_markdown
    reply_markup = InlineKeyboardMarkup(build_vote_keyboard(proposal.id, proposal.kind))
    votes_text = "\n\n*Han votado ya:*\n"
    before_votes_text = text.split(votes_text)[0]

    all_voters = proposal.disliked_by + proposal.liked_by
    voted_admins = [a.user for a in admins if a.user.id in all_voters]
    votes_text += "\n".join([u.name for u in voted_admins])

    final_text = before_votes_text + votes_text
    if final_text != text:
        await callback_query.edit_message_text(
            before_votes_text + votes_text,
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


@log_update
async def handle_callback_query(update: Update, context: CallbackContext):
    global admins
    bot: Bot = context.bot
    admins = admins or await bot.get_chat_administrators(curators_chat_id)
    callback_query: CallbackQuery = update.callback_query
    data: str = callback_query.data
    vote, proposal_id, kind = data.split(":")
    proposal_class = get_proposal_class_by_kind(kind)
    proposal = proposal_class.load(proposal_id)
    required_votes = get_required_votes()

    if callback_query.from_user.id not in [a.user.id for a in admins]:
        await callback_query.answer(
            f"Tener una silla en el consejo no te hace maestro cuñao, {Phrase.get_random_phrase()}"
        )
        return

    if proposal is None:
        await callback_query.answer(
            f"Esa propuesta ha muerto, {Phrase.get_random_phrase()}"
        )
        return

    await _add_vote(proposal, vote, update.callback_query)  # type: ignore

    if len(proposal.liked_by) >= required_votes:
        await _approve_proposal(proposal, callback_query, bot)
    elif len(proposal.disliked_by) >= required_votes:
        await _dismiss_proposal(proposal, callback_query, bot)
    else:
        await _update_proposal_text(proposal, callback_query)
