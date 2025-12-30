from telegram import Bot, ForceReply, InlineKeyboardMarkup, Message, Update, constants
from telegram.ext import CallbackContext

from models.phrase import LongPhrase, Phrase
from models.proposal import LongProposal, Proposal
from services import phrase_service, proposal_service, proposal_repo, long_proposal_repo
from tg.decorators import log_update
from tg.markup.keyboards import build_vote_keyboard
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
    bot: Bot,
    update: Update,
    is_long: bool,
    text: str | None = None,
) -> Message | None:
    if not update.effective_user or not update.effective_message:
        return None

    submitted_by = update.effective_user.name
    proposal = proposal_service.create_from_update(update, is_long=is_long, text=text)

    # Determinar modelos y repositorios según el tipo
    name = LongPhrase.display_name if is_long else Phrase.display_name
    repo = long_proposal_repo if is_long else proposal_repo

    if not proposal.text:
        random_phrase = phrase_service.get_random().text
        return await update.effective_message.reply_text(
            f"¿Qué *{name}* quieres proponer, {random_phrase}?\n"
            "Si no quieres proponer nada, puedes usar /cancelar.",
            reply_markup=ForceReply(selective=True),
            parse_mode=constants.ParseMode.MARKDOWN,
        )

    # Fuzzy search
    most_similar, similarity_ratio = phrase_service.find_most_similar(
        proposal.text, long=is_long
    )

    if similarity_ratio > SIMILARITY_DISCARD_THRESHOLD:
        p1 = phrase_service.get_random().text
        p2 = phrase_service.get_random().text
        text = f"Esa ya la tengo, {p1}, {p2}."
        if similarity_ratio != 100:
            text += f'\nSe parece demasiado a "<b>{most_similar.text}</b>", {phrase_service.get_random().text}.'
        return await update.effective_message.reply_text(
            text, parse_mode=constants.ParseMode.HTML
        )

    repo.save(proposal)
    await _notify_proposal_to_curators(
        bot, proposal, submitted_by, most_similar, similarity_ratio
    )

    return await update.effective_message.reply_text(
        f"Tu aportación será valorada por un consejo de cuñaos expertos y te avisaré una vez haya sido evaluada, "
        f"{phrase_service.get_random().text}.",
        reply_to_message_id=update.effective_message.message_id,
    )


@log_update
async def handle_submit(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.text:
        return

    if len(message.text.split(" ")) > 5:
        p = phrase_service.get_random().text
        await message.reply_text(
            f"¿Estás seguro de que esto es una frase corta, {p}?\n"
            f"Mejor prueba con /proponerfrase {p}.",
            reply_to_message_id=message.message_id,
        )
        return

    await submit_handling(context.bot, update, is_long=False)


@log_update
async def handle_submit_phrase(update: Update, context: CallbackContext) -> None:
    if not update.effective_message:
        return
    await submit_handling(context.bot, update, is_long=True)
