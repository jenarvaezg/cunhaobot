import logging
from functools import wraps
from typing import Any, Callable, TypeVar, cast
from telegram import Chat, Update

from services import phrase_service, user_service
from utils import remove_empty_from_dict

logger = logging.getLogger("cunhaobot")

F = TypeVar("F", bound=Callable[..., object])


def only_admins(f: F) -> F:
    @wraps(f)
    async def wrapper(update: Update, *args: object, **kwargs: object) -> object:
        if not (chat := update.effective_chat):
            return None

        if chat.type == Chat.PRIVATE:
            return await cast(Callable[..., Any], f)(update, *args, **kwargs)

        admins = await chat.get_administrators()
        admin_ids = [admin.user.id for admin in admins]
        if not update.effective_user or update.effective_user.id not in admin_ids:
            if update.effective_message:
                p = (await phrase_service.get_random()).text
                await update.effective_message.reply_text(
                    f"Esto solo lo pueden hacer administradores, {p}.",
                    do_quote=True,
                )
            return None

        return await cast(Callable[..., Any], f)(update, *args, **kwargs)

    return cast(F, wrapper)


def log_update(f: F) -> F:
    @wraps(f)
    async def wrapper(update: Update, *args: object, **kwargs: object) -> object:
        # Actualizar o crear usuario usando el servicio
        await user_service.update_or_create_user(update)

        update_dict = cast(dict[str, object], remove_empty_from_dict(update.to_dict()))
        update_dict["method"] = f.__name__

        logger.info(f"{update_dict}")
        return await cast(Callable[..., Any], f)(update, *args, **kwargs)

    return cast(F, wrapper)
