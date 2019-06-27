import os
from datetime import datetime

from telegram import Bot

curators_chat_id = os.environ.get("MOD_CHAT_ID", "")


def handle_ping(bot: Bot) -> None:
    now = datetime.now()
    bot.send_message(curators_chat_id, f"Son las {now.hour}")
