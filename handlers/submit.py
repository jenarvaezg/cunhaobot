import os

from telegram import Update, Bot, InlineKeyboardMarkup, ParseMode

from markup.keyboards import build_vote_keyboard
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from utils.user import user_from_update

curators_chat_id = os.environ.get("MOD_CHAT_ID", "")

BLACKLIST = [
    'Luis con nombre de usuario Luis0r',
]


def submit_handling(bot: Bot, update: Update, proposal_class: type, phrase_class: type):
    submitted_by = user_from_update(update)

    if submitted_by in BLACKLIST:
        for i in range(100):
            update.message.reply_text(f'Me cago en tu puta madre, {Phrase.get_random_phrase()}')
        bot.send_message(curators_chat_id, f"Le he jodido la vida a '{submitted_by}'")
        return

    proposal = proposal_class.from_update(update)
    if proposal.text == '':
        return update.message.reply_text(
            f'Tienes que decirme una frase, por ejemplo: "/submit {Phrase.get_random_phrase()}"'
            f' o "/submitlong {LongPhrase.get_random_phrase()}"'
        )

    if proposal.text in phrase_class.get_phrases():
        return update.message.reply_text(
            f'Esa ya la tengo, {Phrase.get_random_phrase()}, {Phrase.get_random_phrase()}.')

    proposal.save()

    curators_reply_markup = InlineKeyboardMarkup(build_vote_keyboard(proposal.id, proposal.kind))
    curators_message_text = f"{submitted_by} dice que deberiamos añadir la siguiente {phrase_class.name} a la lista:\n'<b>{proposal.text}</b>'"
    bot.send_message(curators_chat_id, curators_message_text, reply_markup=curators_reply_markup,
                     parse_mode=ParseMode.HTML)
    update.message.reply_text(
        f"Tu aportación será valorada por un consejo de cuñaos expertos y te avisaré una vez haya sido evaluada, {Phrase.get_random_phrase()}")


def handle_submit(bot: Bot, update: Update):
    submit_handling(bot, update, Proposal, Phrase)


def handle_submit_long(bot: Bot, update: Update):
    submit_handling(bot, update, LongProposal, LongPhrase)
