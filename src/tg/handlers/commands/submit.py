from telegram import Bot, ForceReply, InlineKeyboardMarkup, Message, Update, constants
from telegram.ext import CallbackContext

from models.phrase import LongPhrase, Phrase
from models.proposal import LongProposal, Proposal
from services import (
    phrase_service,
    proposal_service,
    proposal_repo,
    long_proposal_repo,
    usage_service,
)
from models.usage import ActionType
from tg.decorators import log_update
from tg.markup.keyboards import build_vote_keyboard
from tg.utils.badges import notify_new_badges
from core.config import config

SIMILARITY_DISCARD_THRESHOLD = 90


async def _notify_proposal_to_curators(
    bot: Bot,
    proposal: Proposal | LongProposal,
    submitted_by: str,
    most_similar: Phrase | LongPhrase,
    similarity_ratio: int,
) -> None:
    curators_reply_markup = InlineKeyboardMarkup(
        build_vote_keyboard(proposal.id, proposal.kind)
    )

    # Determinar nombre del tipo de frase para el mensaje
    name = (
        LongPhrase.display_name
        if isinstance(proposal, LongProposal)
        else Phrase.display_name
    )

    curators_message_text = (
        f"{submitted_by} dice que deberiamos añadir la siguiente {name} a la lista:"
        f"\n'*{proposal.text}*'"
        f"\n\nLa mas parecida es: '*{most_similar.text}*' ({similarity_ratio}%)."
    )

    await bot.send_message(
        config.mod_chat_id,
        curators_message_text,
        reply_markup=curators_reply_markup,
        parse_mode=constants.ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


async def submit_handling(
    update: Update,
    context: CallbackContext,
    is_long: bool,
    text: str | None = None,
) -> Message | None:
    if not update.effective_user or not update.effective_message:
        return None

    bot = context.bot
    submitted_by = update.effective_user.name
    proposal = proposal_service.create_from_update(update, is_long=is_long, text=text)

    # Determinar modelos y repositorios según el tipo
    name = LongPhrase.display_name if is_long else Phrase.display_name

    if not proposal.text:
        random_phrase = (await phrase_service.get_random()).text
        return await update.effective_message.reply_text(
            f"¿Qué *{name}* quieres proponer, {random_phrase}?\n"
            "Si no quieres proponer nada, puedes usar /cancelar.",
            reply_markup=ForceReply(selective=True),
            parse_mode=constants.ParseMode.MARKDOWN,
        )

    # Fuzzy search phrases
    most_similar_phrase, phrase_similarity = await phrase_service.find_most_similar(
        proposal.text, long=is_long
    )

    if phrase_similarity > SIMILARITY_DISCARD_THRESHOLD:
        p_random = (await phrase_service.get_random()).text
        msg = f"Esa ya la tengo aprobada y en la lista, {p_random}."
        if phrase_similarity != 100:
            msg += f"\nSe parece demasiado a: '*{most_similar_phrase.text}*'"

        return await update.effective_message.reply_text(
            msg, parse_mode=constants.ParseMode.MARKDOWN
        )

    # Fuzzy search proposals
    (
        most_similar_proposal,
        proposal_similarity,
    ) = await proposal_service.find_most_similar_proposal(
        proposal.text, is_long=is_long
    )

    if proposal_similarity > SIMILARITY_DISCARD_THRESHOLD and most_similar_proposal:
        p_random = (await phrase_service.get_random()).text
        if most_similar_proposal.voting_ended:
            # Proposal existed and voting ended. Since phrase check passed (didn't exist), it must be rejected.
            return await update.effective_message.reply_text(
                f"Esa propuesta ya pasó por el consejo y fue rechazada, lo siento {p_random}.",
                parse_mode=constants.ParseMode.MARKDOWN,
            )
        else:
            # Proposal exists and voting is active
            return await update.effective_message.reply_text(
                f"Esa frase ya ha sido propuesta y está siendo votada ahora mismo, ten paciencia {p_random}.",
                parse_mode=constants.ParseMode.MARKDOWN,
            )

    if is_long:
        # We know proposal is LongProposal because create_from_update returns LongProposal when is_long=True
        # However, for type checker to be happy without cast, we might need to assert or just ignore if it complains about Union
        # But 'ty' says it's redundant, so it must be inferring it correctly or generic enough.
        # Actually, proposal_service.create_from_update returns Proposal | LongProposal.
        # If 'ty' says cast is redundant, it means it thinks it is ALREADY the target type or compatible.
        # Let's trust 'ty' and remove cast.
        if isinstance(proposal, LongProposal):
            await long_proposal_repo.save(proposal)
        else:
            # Fallback or error logic if needed, but for now assuming correct type
            pass
    else:
        if isinstance(proposal, Proposal):
            await proposal_repo.save(proposal)
    await _notify_proposal_to_curators(
        bot, proposal, submitted_by, most_similar_phrase, phrase_similarity
    )

    # Log usage and check for badges
    new_badges = await usage_service.log_usage(
        user_id=update.effective_user.id,
        platform="telegram",
        action=ActionType.PROPOSE,
        metadata={"is_long": is_long},
    )
    await notify_new_badges(update, context, new_badges)

    return await update.effective_message.reply_text(
        f"Tu aportación será valorada por un consejo de cuñaos expertos y te avisaré una vez haya sido evaluada, "
        f"{(await phrase_service.get_random()).text}.",
        reply_to_message_id=update.effective_message.message_id,
    )


@log_update
async def handle_submit(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.text:
        return

    if len(message.text.split(" ")) > 5:
        p = (await phrase_service.get_random()).text
        await message.reply_text(
            f"¿Estás seguro de que esto es una frase corta, {p}?\n"
            f"Mejor prueba con /proponerfrase {p}.",
            reply_to_message_id=message.message_id,
        )
        return

    await submit_handling(update, context, is_long=False)


@log_update
async def handle_submit_phrase(update: Update, context: CallbackContext) -> None:
    if not update.effective_message:
        return
    await submit_handling(update, context, is_long=True)
