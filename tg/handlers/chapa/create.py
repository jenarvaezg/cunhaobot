from telegram import Update, Bot, Message

from models.schedule import ScheduledTask
from tg.handlers.inline_query.base import get_query_mode, MODE_HANDLERS
from tg.utils.decorators import log_update
from models.phrase import Phrase


def usage(update: Update) -> Message:
    return update.message.reply_text(
        "Para usar el servicio de chapas, tienes que decirme la hora a la que quieres la chapa y, opcionalmente, "
        "puedes añadir parámetros. Ejemplos:\n/chapa 11 <- Saludo aleatorio a las 11 como "
        f"¿Que pasa, {Phrase.get_random_phrase()}?\n/chapa 20 frase <- Frase aleatoria a las 20 (8PM)\n"
        f"/chapa 15 frase mujer <- Frase aleatoria que incluya 'mujer' a las 15 (3PM)",
        quote=True,
    )

@log_update
def handle_create_chapa(bot: Bot, update: Update):
    try:
        tokens = update.message.text.split(" ")
        hour, query = int(tokens[1]), " ".join(tokens[2:])
        if hour > 24:
            return update.message.reply_text(f"{Phrase.get_random_phrase()}, de momento solo soporto horas en punto")
        hour %= 24
    except (KeyError, ValueError, IndexError) as e:
        return usage(update)

    # try to get id the chapa is valid
    query_mode, rest = get_query_mode(query)
    resuls_fn = MODE_HANDLERS.get(query_mode)
    if resuls_fn is None:
        update.message.reply_text(f"No se que hacer con '{query}', {Phrase.get_random_phrase()}", quote=True)
        return usage(update)

    ScheduledTask(update.effective_chat.id, hour, query, service='telegram').save()

    update.message.reply_text(
        f"Configurada chapa a las {hour}. Puedes eliminarla en cualquier momento usando /borrarchapa"
    )
