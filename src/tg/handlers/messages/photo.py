import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.ai_service import ai_service
from services.tts_service import tts_service
from services import usage_service
from models.usage import ActionType
from infrastructure.datastore.chat import chat_repository
from tg.decorators import log_update
from tg.utils.badges import notify_new_badges

logger = logging.getLogger(__name__)


@log_update
async def photo_roast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles photos by generating a vision roast and a voice message."""
    if not (message := update.message) or not message.photo:
        return

    if not update.effective_chat or not update.effective_user:
        return

    # Check for direct interaction (Private chat or Mention in caption)
    is_private = update.effective_chat.type == "private"
    bot_username = context.bot.username
    caption = message.caption.lower() if message.caption else ""
    is_mentioned = bot_username and f"@{bot_username.lower()}" in caption

    if not (is_private or is_mentioned):
        return

    # Premium Check
    chat = await chat_repository.load(update.effective_chat.id)
    if not chat or not chat.is_premium:
        await message.reply_text(
            "⛔️ **Función Premium**\n\n"
            "El análisis de visión (Cuñao Vision) requiere una suscripción activa.\n"
            "Usa /premium para activar la barra libre.",
            parse_mode="Markdown",
        )
        return

    user_id = update.effective_user.id
    logger.info(
        f"Processing photo roast for user {user_id} (Private: {is_private}, Mentioned: {is_mentioned})"
    )

    try:
        # Get the highest resolution photo
        photo = message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()

        # Generate roast text
        roast_text = await ai_service.analyze_image(bytes(image_bytes))

        # Log usage and check for badges
        new_badges = await usage_service.log_usage(
            user_id=user_id, platform="telegram", action=ActionType.VISION
        )

        # Generate audio bytes
        audio_content = tts_service.generate_audio(roast_text)

        # Send voice message (as voice note) with text as caption
        await message.reply_voice(
            voice=audio_content,
            caption=roast_text,
            reply_to_message_id=message.message_id,
        )

        # Notify about new badges if any
        await notify_new_badges(update, context, new_badges)

    except Exception as e:
        logger.error(f"Error in photo_roast handler: {e}")
        await message.reply_text(
            "Mira, eso es una chapuza tan grande que no me deja ni ver la foto."
        )
