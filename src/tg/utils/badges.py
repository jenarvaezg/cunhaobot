import logging
from telegram import Update, constants
from telegram.ext import CallbackContext
from utils.ui import format_badge_notification

logger = logging.getLogger(__name__)


async def notify_new_badges(
    update: Update, context: CallbackContext, new_badges: list
) -> None:
    """Sends a notification for each newly awarded badge."""
    if not new_badges:
        return

    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        return

    for badge in new_badges:
        try:
            text = format_badge_notification(badge)
            if update.effective_message:
                await update.effective_message.reply_text(
                    text, parse_mode=constants.ParseMode.HTML
                )
            else:
                # Fallback to private message (e.g. for inline mode)
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=text,
                        parse_mode=constants.ParseMode.HTML,
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not send private badge notification to {user_id}: {e}"
                    )
        except Exception as e:
            logger.error(f"Error notifying badge {badge.id}: {e}")
