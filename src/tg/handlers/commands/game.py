from telegram import Update
from telegram.ext import CallbackContext

from tg.decorators import log_update


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

    # Prepare the URL for the game.
    # For now, it's a placeholder. Later we will point to our Litestar server.
    # We pass user_id to identify the player.
    user_id = query.from_user.id
    game_url = (
        f"https://{context.bot.username}.uc.r.appspot.com/game/launch?user_id={user_id}"
    )

    # Answer the callback query with the URL.
    # This is what opens the Telegram WebView/Browser.
    await query.answer(url=game_url)
