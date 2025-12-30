from telegram import Message, Update
from telegram.ext import CallbackContext

from models.schedule import Schedule
from services import phrase_service, schedule_repo
from tg.decorators import log_update, only_admins
from tg.handlers.inline.inline_query.base import MODE_HANDLERS, get_query_mode


async def usage(update: Update) -> Message:
    if not update.effective_message:
        raise ValueError("No effective message")

    p = phrase_service.get_random().text
    return await update.effective_message.reply_text(
        "Para usar el servicio de chapas, tienes que decirme la hora a la que quieres la chapa y, opcionalmente, "
        "puedes añadir parámetros. Ejemplos:\n'/chapa 1100' <- Saludo aleatorio a las 11 como "
        f"¿Qué pasa, {p}?\n'/chapa 2030 frase' <- Frase aleatoria a las 20:30 (8:30PM)\n"
        f"'/chapa 1515 frase mujer' <- Frase aleatoria que incluya 'mujer' a las 15:15 (3:15PM).",
        do_quote=True,
    )


def require_valid_query(query: str) -> None:
    query_mode, rest = get_query_mode(query)
    handler = MODE_HANDLERS.get(query_mode)
    if handler is None:
        p = phrase_service.get_random().text
        raise KeyError(f"No entiendo esos parametros: '{query}', {p}.")


def split_time(time_s: str) -> tuple[int, int]:
    try:
        time = int(time_s.replace(":", ""))
    except ValueError:
        p = phrase_service.get_random().text
        raise ValueError(
            f"La hora me la das con puntos o sin ellos, pero sin basura, {p}."
        ) from None

    minute = time % 100
    hour = time // 100
    if minute > 60 or minute < 0:
        p = phrase_service.get_random().text
        raise ValueError(f"Mal valor de minutos, {p}.")
    if hour > 24 or hour < 0:
        p = phrase_service.get_random().text
        raise ValueError(f"Mal valor de horas, {p}.")

    return hour % 24, minute


@only_admins
@log_update
async def handle_create_chapa(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.text:
        return

    text = " ".join(message.text.split())
    tokens = text.split(" ")

    if len(tokens) == 1:
        await usage(update)
        return

    time, query = tokens[1], " ".join(tokens[2:])

    try:
        require_valid_query(query)
        hour, minute = split_time(time)
    except (KeyError, ValueError, IndexError) as e:
        await message.reply_text(str(e), do_quote=True)
        await usage(update)
        return

    if not update.effective_chat or not update.effective_user:
        return

    schedule = Schedule(
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id,
        hour=hour,
        minute=minute,
        query=query,
        service="telegram",
        task_type="chapa",
    )
    schedule_repo.save(schedule)

    await message.reply_text(
        f"Configurada chapa a las {hour:02}:{minute:02}. Puedes eliminarla en cualquier momento usando /borrarchapa.",
        do_quote=True,
    )
