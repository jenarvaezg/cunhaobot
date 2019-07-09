import os
from typing import Union, Type

from telegram import Update, Bot, InlineKeyboardMarkup, ParseMode

from tg.markup.keyboards import build_vote_keyboard
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from tg.decorators import log_update
from tg.utils.user import user_from_update

curators_chat_id = os.environ.get("MOD_CHAT_ID", "")

proposal_t = Union[Type[Proposal], Type[LongProposal]]
phrase_t = Union[Type[Phrase], Type[LongPhrase]]


def submit_handling(bot: Bot, update: Update, proposal_class: proposal_t, phrase_class: phrase_t):
    submitted_by = user_from_update(update)

    proposal = proposal_class.from_update(update)
    if proposal.text == '':
        return update.effective_message.reply_text(
            f'Tienes que decirme una frase, por ejemplo: "/submit {Phrase.get_random_phrase()}"'
            f' o "/submitlong {LongPhrase.get_random_phrase()}".'
        )

    if proposal.text in phrase_class.get_phrases():
        return update.effective_message.reply_text(
            f'Esa ya la tengo, {Phrase.get_random_phrase()}, {Phrase.get_random_phrase()}.')

    proposal.save()

    curators_reply_markup = InlineKeyboardMarkup(build_vote_keyboard(proposal.id, proposal.kind))
    curators_message_text = f"{submitted_by} dice que deberiamos añadir la siguiente {phrase_class.name} a la lista:" \
                            f"\n'<b>{proposal.text}</b>'"
    bot.send_message(curators_chat_id, curators_message_text, reply_markup=curators_reply_markup,
                     parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        f"Tu aportación será valorada por un consejo de cuñaos expertos y te avisaré una vez haya sido evaluada, "
        f"{Phrase.get_random_phrase()}.",
        quote=True,
    )


@log_update
def handle_submit(bot: Bot, update: Update):
    submit_handling(bot, update, Proposal, Phrase)


@log_update
def handle_submit_long(bot: Bot, update: Update):
    submit_handling(bot, update, LongProposal, LongPhrase)
