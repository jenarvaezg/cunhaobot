import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.ai_service import ai_service
from services.tts_service import tts_service
from tg.decorators import log_update

logger = logging.getLogger(__name__)


@log_update
async def photo_roast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles photos by generating a vision roast and a voice message."""
    if not update.message or not update.message.photo:
        return

    if not update.effective_chat or not update.effective_user:
        return

    # Restrict to private chats for now to avoid spam in groups
    if update.effective_chat.type != "private":
        return

    logger.info(f"Processing photo roast for user {update.effective_user.id}")

    try:
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()

        # Generate roast text
        roast_text = await ai_service.analyze_image(bytes(image_bytes))

        # Generate audio bytes
        audio_content = tts_service.generate_audio(roast_text)

        # Send voice message (as voice note) with text as caption
        await update.message.reply_voice(
            voice=audio_content,
            caption=roast_text,
            reply_to_message_id=update.message.message_id,
        )

    except Exception as e:
        logger.error(f"Error in photo_roast handler: {e}")
        await update.message.reply_text(
            "Mira, eso es una chapuza tan grande que no me deja ni ver la foto."
        )
