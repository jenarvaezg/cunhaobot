import os

from telegram import Update, Bot, InlineKeyboardMarkup, ParseMode

from markup.keyboards import build_vote_keyboard
from models.phrase import Phrase
from models.proposal import Proposal
from utils.user import user_from_update

curators_chat_id = os.environ["MOD_CHAT_ID"]

BLACKLIST = [
    'Luis con nombre de usuario Luis0r',
]


def handle_submit(bot: Bot, update: Update):
    submitted_by = user_from_update(update)

    if submitted_by in BLACKLIST:
        for i in range(100):
            update.message.reply_text(f'Me cago en tu puta madre, {Phrase.get_random_phrase()}')
        bot.send_message(curators_chat_id, f"Le he jodido la vida a '{submitted_by}'")
        return

    if update.message.chat.type != 'private':
        return update.message.reply_text(f'No me invoques por grupos {Phrase.get_random_phrase()}')

    proposal = Proposal.from_update(update)
    if proposal.text == '':
        return update.message.reply_text(f'Tienes que decirme una frase, por ejemplo: "/submit {Phrase.get_random_phrase()}"')

    if proposal.text in Phrase.get_phrases():
        return update.message.reply_text('Esa ya la tengo, mastodonte, maestro.')

    proposal.save()

    curators_reply_markup = InlineKeyboardMarkup(build_vote_keyboard(proposal.id))
    curators_message_text = f"{submitted_by} dice que deberiamos añadir la siguiente frase a la lista:\n'<b>{proposal.text}</b>'"
    bot.send_message(curators_chat_id, curators_message_text, reply_markup=curators_reply_markup, parse_mode=ParseMode.HTML)
    update.message.reply_text(
        "Tu aportación será valorada por un consejo de cuñaos expertos y te avisaré una vez haya sido evaluada.")
