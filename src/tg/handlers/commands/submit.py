from telegram import Bot, ForceReply, InlineKeyboardMarkup, Message, Update, constants
from telegram.ext import CallbackContext

from models.phrase import LongPhrase, Phrase
from models.proposal import LongProposal, Proposal
from core.container import services
from models.usage import ActionType
from services.proposal_service import IntakeStatus
from tg.decorators import log_update
from tg.markup.keyboards import build_vote_keyboard
from tg.utils.badges import notify_new_badges
from core.config import config


async def _notify_proposal_to_curators(
    bot: Bot,
    proposal: Proposal | LongProposal,
    submitted_by: str,
    most_similar_text: str,
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
        f"\n\nLa mas parecida es: '*{most_similar_text}*' ({similarity_ratio}%)."
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
    proposal = services.proposal_service.create_from_update(
        update, is_long=is_long, text=text
    )

    # Determinar nombre del tipo de frase para los mensajes
    name = LongPhrase.display_name if is_long else Phrase.display_name

    # The Pieza cuñadil intake module owns the decision; the handler only
    # translates the outcome into a Telegram response.
    result = await services.proposal_service.submit(proposal)

    if result.status is IntakeStatus.EMPTY:
        random_phrase = (await services.phrase_service.get_random()).text
        return await update.effective_message.reply_text(
            f"¿Qué *{name}* quieres proponer, {random_phrase}?\n"
            "Si no quieres proponer nada, puedes usar /cancelar.",
            reply_markup=ForceReply(selective=True),
            parse_mode=constants.ParseMode.MARKDOWN,
        )

    if result.status is IntakeStatus.DUPLICATE_APPROVED:
        p_random = (await services.phrase_service.get_random()).text
        msg = f"Esa ya la tengo aprobada y en la lista, {p_random}."
        if result.similarity != 100:
            msg += f"\nSe parece demasiado a: '*{result.similar_text}*'"
        return await update.effective_message.reply_text(
            msg, parse_mode=constants.ParseMode.MARKDOWN
        )

    if result.status is IntakeStatus.DUPLICATE_REJECTED:
        p_random = (await services.phrase_service.get_random()).text
        return await update.effective_message.reply_text(
            f"Esa propuesta ya pasó por el consejo y fue rechazada, lo siento {p_random}.",
            parse_mode=constants.ParseMode.MARKDOWN,
        )

    if result.status is IntakeStatus.DUPLICATE_ACTIVE:
        p_random = (await services.phrase_service.get_random()).text
        return await update.effective_message.reply_text(
            f"Esa frase ya ha sido propuesta y está siendo votada ahora mismo, ten paciencia {p_random}.",
            parse_mode=constants.ParseMode.MARKDOWN,
        )

    await _notify_proposal_to_curators(
        bot, proposal, submitted_by, result.similar_text, result.similarity
    )

    # Log usage and check for badges
    new_badges = await services.usage_service.log_usage(
        user_id=update.effective_user.id,
        platform="telegram",
        action=ActionType.PROPOSE,
        metadata={"is_long": is_long},
    )
    await notify_new_badges(update, context, new_badges)

    return await update.effective_message.reply_text(
        f"Tu aportación será valorada por un consejo de cuñaos expertos y te avisaré una vez haya sido evaluada, "
        f"{(await services.phrase_service.get_random()).text}.",
        reply_to_message_id=update.effective_message.message_id,
    )


@log_update
async def handle_submit(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.text:
        return

    if len(message.text.split(" ")) > 5:
        p = (await services.phrase_service.get_random()).text
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
