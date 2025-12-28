import logging
from functools import wraps

from telegram import Chat, Update

from models.phrase import Phrase
from models.user import User
from utils import remove_empty_from_dict

logger = logging.getLogger("cunhaobot")


def only_admins(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        if not (chat := update.effective_chat):
            return

        if chat.type == Chat.PRIVATE:
            return await f(update, *args, **kwargs)

        admins = await chat.get_administrators()
        admin_ids = [admin.user.id for admin in admins]
        if not update.effective_user or update.effective_user.id not in admin_ids:
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"Esto solo lo pueden hacer administradores, {Phrase.get_random_phrase()}.",
                    do_quote=True,
                )
            return

        return await f(update, *args, **kwargs)

    return wrapper


def log_update(f):
    @wraps(f)
    async def wrapper(update: Update, *args, **kwargs):
        u = User.update_or_create_from_update(update)
        if u:
            u.save()

        update_dict = remove_empty_from_dict(update.to_dict())
        update_dict["method"] = f.__name__

        logger.info(f"{update_dict}")
        return await f(update, *args, **kwargs)

    return wrapper
