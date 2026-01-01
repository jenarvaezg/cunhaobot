import logging
from telegram import Update
from telegram.ext import CallbackContext
from services import phrase_service, cunhao_agent
from tg.decorators import log_update
from tg.utils.history import get_telegram_history

logger = logging.getLogger(__name__)


@log_update
async def handle_message(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not message.text:
        return

    text = message.text.lower()

    # Check for direct interaction (Private chat, Reply to bot, or Mention)
    bot_username = context.bot.username
    is_private = message.chat.type == "private"
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == context.bot.id
    )
    is_mentioned = bot_username and f"@{bot_username.lower()}" in text

    logger.info(
        f"Checking message triggers: Private={is_private}, Reply={is_reply_to_bot}, Mention={is_mentioned}, Text='{text}'"
    )

    if is_private or is_reply_to_bot or is_mentioned:
        # Use AI Agent
        clean_text = message.text
        if is_mentioned and bot_username:
            # Basic cleanup of the mention handle
            clean_text = clean_text.replace(f"@{bot_username}", "").strip()

        logger.info(f"Triggering CunhaoAgent with text: '{clean_text}'")
        # Indicate typing status
        await message.chat.send_action(action="typing")

        # Get context history from replies and general chat (extracted from context)
        history = await get_telegram_history(message, context)

        response = await cunhao_agent.answer(clean_text, history=history)
        await message.reply_text(response, do_quote=True)
        return

    triggers = ["cuñao", "cuñado", "cuñadismo"]

    if any(t in text for t in triggers):
        # Respond with a random long phrase
        p = phrase_service.get_random(long=True).text
        await message.reply_text(p, do_quote=True)
