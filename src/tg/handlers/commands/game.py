import logging
from telegram import Update
from telegram.ext import CallbackContext

from tg.decorators import log_update
from core.container import services
from core.config import config

logger = logging.getLogger(__name__)


@log_update
async def handle_game_command(update: Update, context: CallbackContext) -> None:
    """Sends the game to the chat."""
    message = update.effective_message
    if not message:
        return

    # game_short_name must match what you registered in BotFather
    await context.bot.send_game(
        chat_id=message.chat_id, game_short_name="palillo_cunhao"
    )


async def handle_game_callback(update: Update, context: CallbackContext) -> None:
    """Handles the 'Play' button on the game message."""
    query = update.callback_query
    if not query or query.game_short_name != "palillo_cunhao":
        return

    # Prepare the URL for the game using the base_url from config.
    user_id = query.from_user.id
    inline_message_id = query.inline_message_id

    # Ensure base_url doesn't end with slash or handle it
    base = config.base_url.rstrip("/")
    game_url = f"{base}/game/launch?user_id={user_id}"

    if inline_message_id:
        game_url += f"&inline_message_id={inline_message_id}"
    elif query.message:
        game_url += (
            f"&chat_id={query.message.chat_id}&message_id={query.message.message_id}"
        )

    # Answer the callback query with the URL.
    # This is what opens the Telegram WebView/Browser.
    try:
        await query.answer(url=game_url)
    except Exception as e:
        logger.error(f"Error answering game callback: {e}")


@log_update
async def handle_top_jugones(update: Update, context: CallbackContext) -> None:
    """Shows the top players based on high scores."""
    message = update.effective_message
    if not message:
        return

    # Load all users and sort by game_high_score
    users = await services.user_repo.load_all()
    top_players = sorted(
        [u for u in users if u.game_high_score > 0],
        key=lambda x: x.game_high_score,
        reverse=True,
    )[:10]

    if not top_players:
        await message.reply_text("Todavía no hay nadie jugando. ¡Sé el primero! /jugar")
        return

    text = "🏆 **TOP JUGONES DEL BAR** 🏆\n\n"
    for i, user in enumerate(top_players, 1):
        name = user.username if user.username else user.name
        text += f"{i}. {name}: {user.game_high_score} pts\n"

    text += "\n¡Dale al /jugar y demuéstrales quién manda!"

    await message.reply_text(text, parse_mode="Markdown")
