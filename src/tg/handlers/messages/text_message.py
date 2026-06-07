import logging
from telegram import Update, ReactionTypeEmoji
from telegram.ext import CallbackContext
from core.container import services
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

    # Check Premium Status
    chat = await services.chat_repo.load(message.chat.id)
    is_premium = chat and chat.is_premium

    if is_private or is_reply_to_bot or is_mentioned:
        if not is_premium:
            await message.reply_text(
                "⛔️ **Función Premium**\n\n"
                "El cuñao conversacional requiere una suscripción activa.\n"
                "Usa /premium para activar la barra libre.",
                parse_mode="Markdown",
            )
            return

        # Use shared Chat interaction behavior (AI answer + AI_ASK Uso).
        clean_text = message.text
        if is_mentioned and bot_username:
            # Basic cleanup of the mention handle
            clean_text = clean_text.replace(f"@{bot_username}", "").strip()

        logger.info(f"Triggering CunhaoAgent with text: '{clean_text}'")
        # Indicate typing status
        await message.chat.send_action(action="typing")

        user_id = message.from_user.id if message.from_user else "unknown"
        reply = await services.chat_interaction_service.answer(
            user_id=user_id, platform="telegram", text=clean_text
        )
        await message.reply_text(reply.text, do_quote=True)
        await notify_new_badges(update, context, reply.new_badges)

    # Smart Reaction (runs for EVERY message) - ONLY PREMIUM
    if is_premium:
        try:
            decision = await services.chat_interaction_service.decide_reaction(
                message.text
            )
            if decision.emoji:
                await message.set_reaction(reaction=ReactionTypeEmoji(decision.emoji))

                # A delivered reaction is a REACTION_RECEIVED Uso.
                reaction_badges = (
                    await services.chat_interaction_service.record_reaction_received(
                        user_id=message.from_user.id
                        if message.from_user
                        else "unknown",
                        platform="telegram",
                    )
                )
                await notify_new_badges(update, context, reaction_badges)
        except Exception as e:
            logger.warning(f"Failed to set reaction: {e}")
