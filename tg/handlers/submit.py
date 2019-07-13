import os
from typing import Union, Type

from telegram import Update, Bot, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from fuzzywuzzy import fuzz

from tg.markup.keyboards import build_vote_keyboard
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from tg.decorators import log_update
from tg.utils.user import user_from_update

curators_chat_id = os.environ.get("MOD_CHAT_ID", "")
SIMILARITY_DISCARD_THRESHOLD = int(os.getenv("PHRASE_DISMISSAL_SIMILARITY_THRESHOLD", 90))
SIMILARITY_WARNING_THRESHOLD = int(os.getenv("PHRASE_WARNING_SIMILARITY_THRESHOLD", 70))

proposal_t = Union[Type[Proposal], Type[LongProposal]]
phrase_t = Union[Type[Phrase], Type[LongPhrase]]


def submit_handling(bot: Bot, update: Update, proposal_class: proposal_t, phrase_class: phrase_t):
    submitted_by = user_from_update(update)

    proposal = proposal_class.from_update(update)
    if proposal.text == '':
        return update.effective_message.reply_text(
            f'Tienes que decirme que quieres proponer, por ejemplo: "/submit {Phrase.get_random_phrase()}"'
            f' o "/submitlong {LongPhrase.get_random_phrase()}".'
        )

    # Fuzzy search. If we have one similar, discard.
    phrases = phrase_class.get_phrases()
    lowercase_proposal = proposal.text.lower()
    warning_phrase = None
    for phrase in phrases:
        similarity_ratio = fuzz.ratio(lowercase_proposal, phrase.lower())
        if SIMILARITY_DISCARD_THRESHOLD < similarity_ratio:
            return update.effective_message.reply_text(
                f'Esa ya la tengo, {Phrase.get_random_phrase()}, {Phrase.get_random_phrase()}. Se parece a {phrase}, {Phrase.get_random_phrase()}')
        if SIMILARITY_WARNING_THRESHOLD < similarity_ratio:
            if warning_phrase is None or warning_phrase[0] < similarity_ratio:
                warning_phrase = (similarity_ratio, phrase)


    proposal.save()

    curators_reply_markup = InlineKeyboardMarkup(build_vote_keyboard(proposal.id, proposal.kind))
    curators_message_text = f"{submitted_by} dice que deberiamos añadir la siguiente {phrase_class.name} a la lista:" \
                            f"\n'<b>{proposal.text}</b>'"
    if warning_phrase is not None:
        curators_message_text +=f"\nSe parece a '<b>{warning_phrase[1]}</b>' ({warning_phrase[0]}%)"
    bot.send_message(curators_chat_id, curators_message_text, reply_markup=curators_reply_markup,
                     parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        f"Tu aportación será valorada por un consejo de cuñaos expertos y te avisaré una vez haya sido evaluada, "
        f"{Phrase.get_random_phrase()}.",
        quote=True,
    )


@log_update
def handle_submit(update: Update, context: CallbackContext):
    if len(update.effective_message.text.split(" ")) > 5:
        return update.effective_message.reply_text(
            f'¿Estás seguro de que esto es una frase corta, {Phrase.get_random_phrase()}?\n'
            f'Mejor prueba con /submitlong {Phrase.get_random_phrase()}.',
            quote=True
        )
    submit_handling(context.bot, update, Proposal, Phrase)


@log_update
def handle_submit_long(update: Update, context: CallbackContext):
    submit_handling(context.bot, update, LongProposal, LongPhrase)
