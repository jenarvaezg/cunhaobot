import logging
import os
import random
from datetime import datetime, timedelta
from typing import Iterable, List

import pytz

from telegram import Bot, ParseMode

from models.report import Report
from models.schedule import ScheduledTask
from models.phrase import Phrase, LongPhrase
from models.user import User, InlineUser
from tg.handlers.inline_query.base import get_query_mode, MODE_HANDLERS, AUDIO_MODE

curators_chat_id = os.environ.get("MOD_CHAT_ID", "")
logger = logging.getLogger('cunhaobot')


def _send_chapas(bot: Bot, tasks: Iterable[ScheduledTask]) -> None:
    errors = []
    for task in tasks:
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
            errors.append((task.datastore_id, e, str(e)))

    if errors:
        bot.send_message(
            curators_chat_id,
            f"{Phrase.get_random_phrase()}s, mandando chapas he tenido estos errores: {errors}.")


def _generate_report(now: datetime.date) -> None:
    # Shuffle so in case of draw for usage of the day it's not always the same
    long_phrases: List[LongPhrase] = random.shuffle(LongPhrase.refresh_cache())
    short_phrases: List[Phrase] = random.shuffle(Phrase.refresh_cache())
    users = User.load_all(ignore_gdpr=True)
    chapas = ScheduledTask.get_tasks(type='chapa')
    inline_users = InlineUser.get_all()
    Report.generate(long_phrases, short_phrases, users, inline_users, chapas, now)
    Phrase.remove_daily_usages()
    LongPhrase.remove_daily_usages()


def _send_report(bot: Bot, now: datetime.date) -> None:
    yesterday = now - timedelta(days=1)
    bef_yesterday = yesterday - timedelta(days=1)
    today_report, yesterday_report = Report.get_at(yesterday), Report.get_at(bef_yesterday)

    longs, longs_delta = today_report.longs, today_report.longs - yesterday_report.longs
    shorts, shorts_delta = today_report.shorts, today_report.shorts - yesterday_report.shorts
    users, user_delta = today_report.users, today_report.users - yesterday_report.users
    groups, groups_delta = today_report.groups, today_report.groups - yesterday_report.groups
    in_users, in_users_delta = today_report.inline_users, today_report.inline_users - yesterday_report.inline_users
    in_uses, in_uses_delta = today_report.inline_usages, today_report.inline_usages - yesterday_report.inline_usages
    gdprs, gdprs_delta = today_report.gdprs, today_report.gdprs - yesterday_report.gdprs
    chapas, chapas_delta = today_report.chapas, today_report.chapas - yesterday_report.chapas
    top_long, top_short = today_report.top_long, today_report.top_short

    def fmt_delta(delta: int) -> str:
        return f'+{delta}' if delta >= 0 else str(delta)

    bot.send_message(
        curators_chat_id,
        f"<b>Resumen del {yesterday.strftime('%Y/%m/%d')}</b>:\n"
        f"Frases largas: {longs} ({fmt_delta(longs_delta)})\n"
        f"Palabras poderosas: {shorts} ({fmt_delta(shorts_delta)})\n"
        f"Usuarios: {users} ({fmt_delta(user_delta)})\n"
        f"Grupos: {groups} ({fmt_delta(groups_delta)})\n"
        f"Usuarios inline: {in_users} ({fmt_delta(in_users_delta)})\n"
        f"Usos inline: {in_uses} ({fmt_delta(in_uses_delta)})\n"
        f"Chapas: {chapas} ({fmt_delta(chapas_delta)})\n"
        f"GDPRs: {gdprs} ({fmt_delta(gdprs_delta)})\n\n",
        f"La frase más usada de ayer fue:\n<bold>{top_long}</bold>\n",
        f"El apelativo más usado ayer fue:\n<bold>{top_short}</bold>\n",
        parse_mode=ParseMode.HTML,
    )


def handle_ping(bot: Bot):
    madrid_timezone = pytz.timezone('Europe/Madrid')
    now = datetime.now().astimezone(madrid_timezone)

    _send_chapas(bot, ScheduledTask.get_tasks(hour=now.hour, minute=now.minute, service='telegram', type='chapa'))
    if now.hour == 0 and now.minute == 0:
        _generate_report(now.date() - timedelta(minutes=1))
    elif now.hour == 7 and now.minute == 0:
        _send_report(bot, now.date())



