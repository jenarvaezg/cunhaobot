import logging
from telegram import Update, ReactionTypeEmoji
from telegram.ext import CallbackContext
from services import cunhao_agent, usage_service, ai_service
from models.usage import ActionType
from tg.decorators import log_update
from tg.utils.badges import notify_new_badges

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

        response = await cunhao_agent.answer(clean_text)
        new_badges = await usage_service.log_usage(
            user_id=message.from_user.id if message.from_user else "unknown",
            platform="telegram",
            action=ActionType.AI_ASK,
        )
        await message.reply_text(response, do_quote=True)
        await notify_new_badges(update, context, new_badges)

    # Smart Reaction (runs for EVERY message)
    try:
        reaction_emoji = await ai_service.analyze_sentiment_and_react(message.text)
        if reaction_emoji:
            await message.set_reaction(reaction=ReactionTypeEmoji(reaction_emoji))

            # Log usage for "Centro de Atención" badge
            reaction_badges = await usage_service.log_usage(
                user_id=message.from_user.id if message.from_user else "unknown",
                platform="telegram",
                action=ActionType.REACTION_RECEIVED,
            )
            await notify_new_badges(update, context, reaction_badges)
    except Exception as e:
        logger.warning(f"Failed to set reaction: {e}")
