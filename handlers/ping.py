import os
from datetime import datetime
import pytz

from telegram import Bot

curators_chat_id = os.environ.get("MOD_CHAT_ID", "")


def handle_ping(bot: Bot) -> None:
    madrid_timezone = pytz.timezone('Europe/Madrid')
    now = datetime.now().astimezone(madrid_timezone)
    bot.send_message(curators_chat_id, f"Son las {now.hour}")
