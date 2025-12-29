import asyncio
from typing import Dict
from telegram import Bot
from telegram.error import TelegramError

# Simple in-memory cache for user names
_user_cache: Dict[int, str] = {}
_lock = asyncio.Lock()


async def resolve_user_name(user_id: int, bot: Bot) -> str:
    """Resolves a Telegram user ID to a name, using a cache to avoid spamming the API."""
    if user_id == 0:
        return "Anónimo"

    async with _lock:
        if user_id in _user_cache:
            return _user_cache[user_id]

    try:
        chat = await bot.get_chat(user_id)
        name = chat.full_name or chat.username or f"Usuario {user_id}"

        async with _lock:
            _user_cache[user_id] = name
        return name
    except TelegramError:
        return f"Desconocido ({user_id})"
