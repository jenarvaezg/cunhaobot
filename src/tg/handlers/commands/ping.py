import logging
from typing import Any
from collections.abc import Iterable
from datetime import date, datetime, timedelta
import pytz
from telegram import Bot, constants

from services import phrase_service, report_service, report_repo, schedule_repo
from tg.handlers.inline.inline_query.base import MODE_HANDLERS
from tg.text_router import AUDIO_MODE, STICKER_MODE, get_query_mode
from core.config import config

logger = logging.getLogger("cunhaobot")


async def _send_chapas(bot: Bot, tasks: Iterable[Any]) -> None:
    errors = []
    for task in tasks:
        try:
            # Note: task is now a Schedule struct
            query_mode, rest = get_query_mode(task.query)
            results_fn = MODE_HANDLERS.get(query_mode)

            if not results_fn:
                continue

            result = next(iter(results_fn(rest)), None)

            if result is None or "-bad-search-" in result.id:
                p = phrase_service.get_random().text
                await bot.send_message(
                    task.chat_id,
                    f"Te tengo que dar la chapa, pero no he encontrado nada con los parametros '{task.query}', así que "
                    f"aqui tienes algo parecido, {p}.",
                )
                await bot.send_message(
                    task.chat_id, phrase_service.get_random(long=True).text
                )
                continue

            match query_mode:
                case s if s == AUDIO_MODE:
                    await bot.send_voice(task.chat_id, result.voice_url)
                case s if s == STICKER_MODE:
                    await bot.send_sticker(task.chat_id, result.sticker_file_id)
                case _:
                    await bot.send_message(
                        task.chat_id, result.input_message_content.message_text
                    )
        except Exception as e:
            logger.exception("Error sending chapa")
            errors.append((task.id, e, str(e)))

    if errors:
        p = phrase_service.get_random().text
        await bot.send_message(
            config.mod_chat_id,
            f"{p}s, mandando chapas he tenido estos errores: {errors}.",
        )


async def _send_report(bot: Bot, now: date) -> None:
    yesterday = now - timedelta(days=1)
    bef_yesterday = yesterday - timedelta(days=1)

    today_report = report_repo.get_at(yesterday)
    yesterday_report = report_repo.get_at(bef_yesterday)

    if not today_report or not yesterday_report:
        return

    # Helper for formatting deltas
    def fmt(curr, prev):
        delta = curr - prev
        return f"{curr} ({'+' if delta >= 0 else ''}{delta})"

    await bot.send_message(
        config.mod_chat_id,
        f"<b>Resumen del {yesterday.strftime('%Y/%m/%d')}</b>:\n"
        f"Frases largas: {fmt(today_report.longs, yesterday_report.longs)}\n"
        f"Palabras poderosas: {fmt(today_report.shorts, yesterday_report.shorts)}\n"
        f"Usuarios: {fmt(today_report.users, yesterday_report.users)}\n"
        f"Grupos: {fmt(today_report.groups, yesterday_report.groups)}\n"
        f"Usuarios inline: {fmt(today_report.inline_users, yesterday_report.inline_users)}\n"
        f"Usos inline: {fmt(today_report.inline_usages, yesterday_report.inline_usages)}\n"
        f"Chapas: {fmt(today_report.chapas, yesterday_report.chapas)}\n"
        f"GDPRs: {fmt(today_report.gdprs, yesterday_report.gdprs)}\n\n"
        f"La frase más usada de ayer fue:\n<b>{today_report.top_long}</b>\n"
        f"El apelativo más usado ayer fue:\n<b>{today_report.top_short}</b>\n",
        parse_mode=constants.ParseMode.HTML,
    )


async def handle_ping(bot: Bot) -> None:
    madrid_timezone = pytz.timezone("Europe/Madrid")
    now = datetime.now().astimezone(madrid_timezone)

    # Nota: He simplificado la obtención de tareas para usar el repositorio directamente
    # En el futuro esto podría ir a un ScheduleService
    all_tasks = schedule_repo.load_all()
    active_chapas = [
        t
        for t in all_tasks
        if t.active and t.hour == now.hour and t.minute == now.minute
    ]

    await _send_chapas(bot, active_chapas)

    match (now.hour, now.minute):
        case (23, 59):
            # Obtener chapas para el reporte
            chapas = [t for t in all_tasks if t.active]
            report_service.generate_report(now.date(), chapas)
            # Limpiar usos diarios
            from services import phrase_repo, long_phrase_repo

            phrase_repo.remove_daily_usages()
            long_phrase_repo.remove_daily_usages()
        case (7, 0):
            await _send_report(bot, now.date())
