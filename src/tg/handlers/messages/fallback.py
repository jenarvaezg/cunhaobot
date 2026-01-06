import random
import logging
from telegram import Update, User as TGUser, Bot
from telegram.ext import CallbackContext
from core.container import services
from tg.decorators import log_update

logger = logging.getLogger(__name__)


async def _on_kick(chat_id: int) -> None:
    user = await services.user_repo.load(chat_id)
    if user:
        user.gdpr = True
        await services.user_repo.save(user)


async def _on_other_kicked(bot: Bot, user: TGUser, chat_id: int) -> None:
    p = (await services.phrase_service.get_random()).text
    await bot.send_message(
        chat_id, f"Vaya {p} el {user.name or user.first_name}, ya me jodería."
    )


async def _on_join(bot: Bot, chat_id: int) -> None:
    p = (await services.phrase_service.get_random()).text
    await bot.send_message(
        chat_id,
        "¡Muchas gracias por meterme en el grupo! Te recomiendo usar /help para explicarte qué puedo hacer, "
        f"{p}.",
    )


async def _on_other_joined(bot: Bot, user: TGUser, chat_id: int) -> None:
    n_words = random.choice([2, 3, 4])
    random_phrases = [
        (await services.phrase_service.get_random()).text for _ in range(n_words)
    ]
    phrases = [user.name or user.first_name] + random_phrases
    await bot.send_message(chat_id, ", ".join(phrases) + "!")


def _on_migrate(from_chat_id: int, to_chat_id: int) -> None:
    pass


@log_update
async def handle_fallback_message(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    bot = context.bot
    me = await bot.get_me()

    if message.left_chat_member:
        if message.left_chat_member.username == me.username:
            await _on_kick(message.chat_id)
        else:
            await _on_other_kicked(bot, message.left_chat_member, message.chat_id)

    elif message.new_chat_members:
        for user in message.new_chat_members:
            if user.username == me.username:
                await _on_join(bot, message.chat_id)
            else:
                await _on_other_joined(bot, user, message.chat_id)

    elif message.migrate_to_chat_id:
        _on_migrate(message.chat_id, message.migrate_to_chat_id)

    elif message.migrate_from_chat_id:
        _on_migrate(message.migrate_from_chat_id, message.chat_id)
