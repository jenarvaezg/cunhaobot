import logging
import random
from io import BytesIO
from telegram import Bot
from utils.gcp import get_bucket
from core.config import config

logger = logging.getLogger(__name__)


class StoryService:
    async def post_random_story(self, bot: Bot) -> str:
        """
        Picks a random phrase that has a generated image in GCS and posts it as a Telegram Story.
        """
        from services import phrase_service

        try:
            bucket = get_bucket()
            # List blobs in the generated_images directory
            blobs = list(bucket.list_blobs(prefix="generated_images/"))

            # Filter only PNG images
            image_blobs = [b for b in blobs if b.name.endswith(".png")]

            if not image_blobs:
                return "No hay imágenes generadas en el almacén, fiera."

            # Pick a random image
            selected_blob = random.choice(image_blobs)
            logger.info(f"Selected image for story: {selected_blob.name}")

            # Try to extract phrase ID from filename (generated_images/{id}.png)
            phrase_id = selected_blob.name.split("/")[-1].split(".")[0]
            phrase_text = ""

            try:
                # Load phrase info to use as caption if possible
                phrase = phrase_service.phrase_repo.load(
                    phrase_id
                ) or phrase_service.long_repo.load(phrase_id)
                if phrase:
                    phrase_text = phrase.text
            except Exception:
                logger.warning(f"Could not load phrase info for ID {phrase_id}")

            # Download image data
            image_data = selected_blob.download_as_bytes()

            # Post story to the bot's own account (or a channel if mod_chat_id is a channel)
            # Bots can post stories to themselves or to channels they admin.
            # We'll use the bot's own stories first.
            # Note: bot.send_story is available in recent versions of PTB
            # Using the bot's ID as chat_id sends it to its own story.
            bot_info = await bot.get_me()

            # Prepare the file
            photo_file = BytesIO(image_data)

            # Caption limited to 200 chars for stories usually
            caption = (
                f" sabiduría del día: {phrase_text}" if phrase_text else "¡Buenos días!"
            )
            if len(caption) > 200:
                caption = caption[:197] + "..."

            # Send the story
            # In Telegram Bot API, sendStory requires a 'photo' or 'video'
            # Documentation: https://core.telegram.org/bots/api#sendstory
            # Using direct API call if PTB wrapper is not updated or just send it
            await bot.send_photo(
                chat_id=config.mod_chat_id,
                photo=photo_file,
                caption=f"🚀 PROBANDO STORY (Enviado a mod chat por ahora):\n{caption}",
            )

            # NOTE: sendStory is actually for posting STORIES, but many bots use
            # sendPhoto to a channel that then appears in stories.
            # To post a REAL story:
            try:
                # This might fail if the bot doesn't have Premium or the library version is old
                # but we try the official method
                await bot.send_story(  # type: ignore[unresolved-attribute]
                    chat_id=bot_info.id,
                    photo=photo_file,
                    caption=caption,
                )
                return (
                    f"¡Story publicada con éxito, cuñao! Frase: {phrase_text[:30]}..."
                )
            except Exception as e:
                logger.warning(
                    f"Official send_story failed: {e}. Falling back to mod chat."
                )
                return f"No he podido publicar la Story real (¿Falta Premium?), pero te la he enviado al grupo de moderación. Frase: {phrase_text[:30]}..."

        except Exception as e:
            logger.error("Error posting random story:", exc_info=True)
            return f"Vaya chapuza, ha fallado lo de la story: {str(e)}"


story_service = StoryService()
