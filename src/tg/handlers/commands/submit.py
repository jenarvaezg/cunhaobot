import os

from telegram import Bot, ForceReply, InlineKeyboardMarkup, Message, Update, constants
from telegram.ext import CallbackContext

from models.phrase import LongPhrase, Phrase
from models.proposal import LongProposal, Proposal
from tg.decorators import log_update
from tg.markup.keyboards import build_vote_keyboard

curators_chat_id = os.environ.get("MOD_CHAT_ID", "")
SIMILARITY_DISCARD_THRESHOLD = int(
    os.getenv("PHRASE_DISMISSAL_SIMILARITY_THRESHOLD", 90)
)

proposal_t = type[Proposal] | type[LongProposal]
phrase_t = type[Phrase] | type[LongPhrase]


async def _notify_proposal_to_curators(
    bot: Bot,
    proposal: Proposal,
    submitted_by: str,
    most_similar: Phrase,
    similarity_ratio: int,
) -> None:
    curators_reply_markup = InlineKeyboardMarkup(
        build_vote_keyboard(proposal.id, proposal.kind)
    )
    curators_message_text = (
        f"{submitted_by} dice que deberiamos añadir la siguiente {most_similar.name} a la lista:"
        f"\n'*{proposal.text}*'"
        f"\n\nLa mas parecida es: '*{most_similar}*' ({similarity_ratio}%)."
    )

    await bot.send_message(
        curators_chat_id,
        curators_message_text,
        reply_markup=curators_reply_markup,
        parse_mode=constants.ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


async def submit_handling(
    bot: Bot,
    update: Update,
    proposal_class: proposal_t,
    phrase_class: phrase_t,
    text: str | None = None,
) -> Message:
    if not update.effective_user or not update.effective_message:
        raise ValueError("Update has no effective user or message")
    submitted_by = update.effective_user.name
    proposal = proposal_class.from_update(update, text=text)
    if not proposal.text:
        return await update.effective_message.reply_text(
            f"¿Qué *{phrase_class.name}* quieres proponer, {Phrase.get_random_phrase()}?\n"
            "Si no quieres proponer nada, puedes usar /cancelar.",
            reply_markup=ForceReply(selective=True),
            parse_mode=constants.ParseMode.MARKDOWN,
        )

    # Fuzzy search. If we have one similar, discard.
    most_similar, similarity_ratio = phrase_class.get_most_similar(proposal.text)
    if SIMILARITY_DISCARD_THRESHOLD < similarity_ratio:
        text = f"Esa ya la tengo, {Phrase.get_random_phrase()}, {Phrase.get_random_phrase()}."
        if similarity_ratio != 100:
            text += f'\nSe parece demasiado a "<b>{most_similar}</b>", {Phrase.get_random_phrase()}.'
        return await update.effective_message.reply_text(
            text, parse_mode=constants.ParseMode.HTML
        )

    proposal.save()
    await _notify_proposal_to_curators(
        bot, proposal, submitted_by, most_similar, similarity_ratio
    )

    return await update.effective_message.reply_text(
        f"Tu aportación será valorada por un consejo de cuñaos expertos y te avisaré una vez haya sido evaluada, "
        f"{Phrase.get_random_phrase()}.",
        do_quote=True,
    )


@log_update
async def handle_submit(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.text:
        return

    if len(message.text.split(" ")) > 5:
        await message.reply_text(
            f"¿Estás seguro de que esto es una frase corta, {Phrase.get_random_phrase()}?\n"
            f"Mejor prueba con /proponerfrase {Phrase.get_random_phrase()}.",
            do_quote=True,
        )
        return

    await submit_handling(context.bot, update, Proposal, Phrase)


@log_update
async def handle_submit_phrase(update: Update, context: CallbackContext) -> None:
    if not update.effective_message:
        return
    await submit_handling(context.bot, update, LongProposal, LongPhrase)
