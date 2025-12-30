import logging
from typing import Any
from datetime import datetime
from telegram import (
    Bot,
    CallbackQuery,
    ChatMember,
    InlineKeyboardMarkup,
    Update,
    constants,
)
from telegram.ext import CallbackContext

from models.proposal import Proposal, LongProposal
from services import proposal_service, phrase_service, proposal_repo, long_proposal_repo
from tg.constants import LIKE
from tg.decorators import log_update
from tg.markup.keyboards import build_vote_keyboard
from core.config import config

logger = logging.getLogger(__name__)

admins: list[ChatMember] = []  # Global cache


def get_required_votes() -> int:
    return len(admins) // 2 + 1


def get_vote_summary(proposal: Proposal) -> str:
    likers = [a.user.name for a in admins if a.user.id in proposal.liked_by]
    dislikers = [a.user.name for a in admins if a.user.id in proposal.disliked_by]
    return (
        f"Han votado que si: {' '.join(likers)}\n"
        f"Han votado que no: {' '.join(dislikers)}"
    )


async def _add_vote(
    proposal: Proposal | LongProposal, vote: str, callback_query: CallbackQuery
) -> None:
    proposal_service.vote(proposal, callback_query.from_user.id, vote == LIKE)
    await callback_query.answer(f"Tu voto: {vote} ha sido añadido.")


async def _ensure_admins(bot: Bot) -> None:
    global admins
    if not admins:
        try:
            admins = list(await bot.get_chat_administrators(config.mod_chat_id))
        except Exception as e:
            logger.warning(f"Could not fetch admins: {e}")


async def approve_proposal(
    proposal: Proposal | LongProposal,
    bot: Bot,
    callback_query: CallbackQuery | None = None,
) -> None:
    await _ensure_admins(bot)

    proposal.voting_ended = True
    proposal.voting_ended_at = datetime.now()

    repo = long_proposal_repo if isinstance(proposal, LongProposal) else proposal_repo
    repo.save(proposal)

    p_random = phrase_service.get_random().text
    msg_text = (
        f"La propuesta '{proposal.text}' queda formalmente aprobada y añadida a la lista.\n\n"
        f"{get_vote_summary(proposal)}"
    )

    if callback_query:
        await callback_query.edit_message_text(msg_text, disable_web_page_preview=True)
    else:
        try:
            await bot.send_message(
                config.mod_chat_id, f"✅ APROBADA DESDE WEB\n\n{msg_text}"
            )
        except Exception as e:
            logger.error(f"Error sending web approval notification: {e}")

    if proposal.from_chat_id > 0:
        try:
            await bot.send_message(
                proposal.from_chat_id,
                f"Tu propuesta '{proposal.text}' ha sido aprobada, felicidades, {p_random}",
                reply_to_message_id=proposal.from_message_id or None,
            )
        except Exception as e:
            logger.error(f"Error enviando notificación de aprobación: {e}")

    # Delegar creación de la frase al servicio
    await phrase_service.create_from_proposal(proposal, bot)


async def dismiss_proposal(
    proposal: Proposal | LongProposal,
    bot: Bot,
    callback_query: CallbackQuery | None = None,
) -> None:
    await _ensure_admins(bot)

    proposal.voting_ended = True
    proposal.voting_ended_at = datetime.now()

    repo = long_proposal_repo if isinstance(proposal, LongProposal) else proposal_repo
    repo.save(proposal)

    p_random = phrase_service.get_random().text
    msg_text = (
        f"La propuesta '{proposal.text}' queda formalmente rechazada.\n\n"
        f"{get_vote_summary(proposal)}"
    )

    if callback_query:
        await callback_query.edit_message_text(msg_text, disable_web_page_preview=True)
    else:
        try:
            await bot.send_message(
                config.mod_chat_id, f"❌ RECHAZADA DESDE WEB\n\n{msg_text}"
            )
        except Exception as e:
            logger.error(f"Error sending web dismissal notification: {e}")

    if proposal.from_chat_id > 0:
        try:
            await bot.send_message(
                proposal.from_chat_id,
                f"Tu propuesta '{proposal.text}' ha sido rechazada, lo siento {p_random}",
                reply_to_message_id=proposal.from_message_id or None,
            )
        except Exception as e:
            logger.error(f"Error enviando notificación de rechazo: {e}")

    repo.delete(proposal.id)


async def _update_proposal_text(
    proposal: Proposal | LongProposal, callback_query: CallbackQuery
) -> None:
    if not callback_query.message or not hasattr(
        callback_query.message, "text_markdown"
    ):
        return

    message: Any = callback_query.message
    text = getattr(message, "text_markdown", "")
    if not isinstance(text, str):
        return

    reply_markup = InlineKeyboardMarkup(build_vote_keyboard(proposal.id, proposal.kind))
    votes_text = "\n\n*Han votado ya:*\n"
    before_votes_text = text.split(votes_text)[0]

    all_voters = proposal.disliked_by + proposal.liked_by
    voted_admins = [a.user for a in admins if a.user.id in all_voters]
    votes_text += "\n".join([u.name for u in voted_admins])

    final_text = before_votes_text + votes_text
    if final_text == text:
        return

    await callback_query.edit_message_text(
        final_text,
        reply_markup=reply_markup,
        parse_mode=constants.ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


@log_update
async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    global admins
    if not (callback_query := update.callback_query) or not (
        data := callback_query.data
    ):
        return

    bot: Bot = context.bot
    admins = admins or list(await bot.get_chat_administrators(config.mod_chat_id))

    if callback_query.from_user.id not in [a.user.id for a in admins]:
        p = phrase_service.get_random().text
        await callback_query.answer(
            f"Tener una silla en el consejo no te hace maestro cuñao, {p}"
        )
        return

    vote, proposal_id, kind = data.split(":")
    repo = long_proposal_repo if kind == LongProposal.kind else proposal_repo
    proposal = repo.load(proposal_id)

    if proposal is None:
        p = phrase_service.get_random().text
        await callback_query.answer(f"Esa propuesta ha muerto, {p}")
        return

    await _add_vote(proposal, vote, callback_query)

    required_votes = get_required_votes()
    if len(proposal.liked_by) >= required_votes:
        await approve_proposal(proposal, bot, callback_query)
        return

    if len(proposal.disliked_by) >= required_votes:
        await dismiss_proposal(proposal, bot, callback_query)
        return

    await _update_proposal_text(proposal, callback_query)
