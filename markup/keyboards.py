from typing import List
from telegram import InlineKeyboardButton

from constants import LIKE, DISLIKE


def build_vote_keyboard(message_id: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(LIKE, callback_data=f"{LIKE}:{message_id}"),
            InlineKeyboardButton(DISLIKE, callback_data=f"{DISLIKE}:{message_id}")
        ]
    ]
