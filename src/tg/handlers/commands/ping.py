import logging
from datetime import datetime
import pytz
from telegram import Bot

logger = logging.getLogger("cunhaobot")


async def handle_ping(bot: Bot) -> None:
    madrid_timezone = pytz.timezone("Europe/Madrid")
    now = datetime.now().astimezone(madrid_timezone)
    logger.info(f"Ping received at {now}")
