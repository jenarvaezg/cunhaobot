import logging
from telegram import Update, constants
from telegram.ext import CallbackContext
from utils.ui import format_badge_notification

logger = logging.getLogger(__name__)


async def notify_new_badges(
    update: Update, context: CallbackContext, new_badges: list
) -> None:
    """Sends a notification for each newly awarded badge."""
    if not new_badges or not update.effective_message:
        return

    for badge in new_badges:
        try:
            text = format_badge_notification(badge)
            await update.effective_message.reply_text(
                text, parse_mode=constants.ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying badge {badge.id}: {e}")
