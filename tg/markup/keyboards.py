from typing import List
from telegram import InlineKeyboardButton

from tg.constants import LIKE, DISLIKE


def build_vote_keyboard(
    message_id: str, proposal_kind: str
) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                LIKE, callback_data=f"{LIKE}:{message_id}:{proposal_kind}"
            ),
            InlineKeyboardButton(
                DISLIKE, callback_data=f"{DISLIKE}:{message_id}:{proposal_kind}"
            ),
        ]
    ]
