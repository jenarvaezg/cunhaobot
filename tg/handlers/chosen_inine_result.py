from telegram import Bot, Update

from models.user import InlineUser
from tg.decorators import log_update


@log_update
def handle_chosen_inline_result(bot: Bot, update: Update):
    InlineUser.update_or_create_from_update(update).add_usage()

