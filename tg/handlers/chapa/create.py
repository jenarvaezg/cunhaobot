from typing import Tuple

from telegram import Update, Message
from telegram.ext import CallbackContext

from models.schedule import ScheduledTask
from tg.handlers.inline_query.base import get_query_mode, MODE_HANDLERS
from tg.decorators import log_update, only_admins
from models.phrase import Phrase


def usage(update: Update) -> Message:
    return update.effective_message.reply_text(
        "Para usar el servicio de chapas, tienes que decirme la hora a la que quieres la chapa y, opcionalmente, "
        "puedes añadir parámetros. Ejemplos:\n'/chapa 1100' <- Saludo aleatorio a las 11 como "
        f"¿Qué pasa, {Phrase.get_random_phrase()}?\n'/chapa 2030 frase' <- Frase aleatoria a las 20:30 (8:30PM)\n"
        f"'/chapa 1515 frase mujer' <- Frase aleatoria que incluya 'mujer' a las 15:15 (3:15PM).",
        quote=True,
    )


def require_valid_query(query: str) -> None:
    query_mode, rest = get_query_mode(query)
    handler = MODE_HANDLERS.get(query_mode)  # Raise KeyError if not here
    if handler is None:
        raise KeyError(
            f"No entiendo esos parametros: '{query}', {Phrase.get_random_phrase()}."
        )


def split_time(time_s: str) -> Tuple[int, int]:
    try:
        time = int(time_s.replace(":", ""))
    except ValueError:
        raise ValueError(
            f"La hora me la das con puntos o sin ellos, pero sin basura, {Phrase.get_random_phrase()}."
        )

    minute = time % 100
    hour = time // 100
    if minute > 60 or minute < 0:
        raise ValueError(f"Mal valor de minutos, {Phrase.get_random_phrase()}.")
    if hour > 24 or hour < 0:
        raise ValueError(f"Mal valor de horas, {Phrase.get_random_phrase()}.")

    return hour % 24, minute


@only_admins
@log_update
def handle_create_chapa(update: Update, context: CallbackContext):
    text = " ".join(update.effective_message.text.split())

    try:
        tokens = text.split(" ")
        if len(tokens) == 1:
            return usage(update)
        time, query = tokens[1], " ".join(tokens[2:])
    except (KeyError, ValueError, IndexError) as e:
        update.effective_message.reply_text(str(e), quote=True)
        return usage(update)

    try:
        require_valid_query(query)
        hour, minute = split_time(time)
    except (KeyError, ValueError) as e:
        update.effective_message.reply_text(str(e), quote=True)
        return usage(update)

    ScheduledTask(
        update.effective_chat.id,
        hour,
        minute,
        query,
        service="telegram",
        task_type="chapa",
    ).save()

    update.effective_message.reply_text(
        f"Configurada chapa a las {hour:02}:{minute:02}. Puedes eliminarla en cualquier momento usando /borrarchapa.",
        quote=True,
    )
