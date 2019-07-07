import logging
import os
from datetime import datetime
import pytz

from telegram import Bot

from models.schedule import ScheduledTask
from models.phrase import Phrase, LongPhrase
from tg.handlers.inline_query.base import get_query_mode, MODE_HANDLERS, AUDIO_MODE

curators_chat_id = os.environ.get("MOD_CHAT_ID", "")
logger = logging.getLogger('cunhaobot')


def handle_ping(bot: Bot):
    madrid_timezone = pytz.timezone('Europe/Madrid')
    now = datetime.now().astimezone(madrid_timezone)
    scheduled_tasks = ScheduledTask.get_tasks(hour=now.hour, minute=now.minute, service="telegram")
    errors = []
    for task in scheduled_tasks:
        try:
            query_mode, rest = get_query_mode(task.query)
            resuls_fn = MODE_HANDLERS.get(query_mode)
            result = next(iter(resuls_fn(rest)), None)
            if result is None:
                bot.send_message(
                    task.chat_id,
                    f"No he encontrado nada con los parametros '{task.query}', así que "
                    f"aqui tienes algo parecido, {Phrase.get_random_phrase()}."
                )
                bot.send_message(task.chat_id, LongPhrase.get_random_phrase())
                continue
            if query_mode == AUDIO_MODE:
                bot.send_voice(task.chat_id, result.voice_url)
            else:
                bot.send_message(task.chat_id, result.input_message_content.message_text)
        except Exception as e:
            logger.exception("Error sending chapa")
            errors.append((task.datastore_id, e))

    if errors:
        bot.send_message(
            curators_chat_id,
            f"{Phrase.get_random_phrase()}s, mandando chapas he tenido estos errores: {errors}.")

