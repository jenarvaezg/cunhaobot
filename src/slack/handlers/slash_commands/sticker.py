import requests
import logging
from services.phrase_service import PhraseService
from utils.image_utils import generate_png
from core.config import config

logger = logging.getLogger(__name__)


def handle_sticker(slack_data: dict, phrase_service: PhraseService) -> dict:
    text = slack_data.get("text", "")
    channel_id = slack_data.get("channel_id")

    logger.info(f"Handling sticker request for text: '{text}' in channel: {channel_id}")

    if text:
        phrases = phrase_service.get_phrases(search=text, long=True)
        if not phrases:
            # Try fuzzy search if no exact contains match
            phrase, score = phrase_service.find_most_similar(text, long=True)
            if score < 60:  # Threshold for similarity
                logger.warning(
                    f"No phrase found for '{text}'. Most similar: '{phrase.text}' ({score}%)"
                )
                return {
                    "indirect": {
                        "text": f'No tengo ninguna frase que encaje con "{text}". ¿Querías decir algo como "{phrase.text}"?'
                    },
                    "direct": "",
                }
        else:
            import random

            phrase = random.choice(phrases)
    else:
        phrase = phrase_service.get_random(long=True)

    if not phrase:
        logger.error("No phrases available in the database")
        return {
            "indirect": {"text": "No hay frases disponibles en este momento."},
            "direct": "",
        }

    logger.info(f"Generating sticker for phrase: '{phrase.text}'")
    sticker_image = generate_png(phrase.text)

    try:
        # Use requests to upload the file to Slack
        # Note: files.upload is deprecated, but let's stick to it for now if it worked before
        # or check if it needs to be updated to files.uploadV2
        logger.info(f"Uploading sticker to Slack channel {channel_id}...")

        if not config.slack_bot_token:
            logger.error("SLACK_BOT_TOKEN is not configured!")

        response = requests.post(
            "https://slack.com/api/files.upload",
            params={
                "token": config.slack_bot_token,
                "channels": channel_id,
                "initial_comment": f'Aquí tienes tu sticker con la frase: "{phrase.text}"',
            },
            files={"file": ("sticker.png", sticker_image.getvalue(), "image/png")},
            timeout=10,
        )

        resp_json = response.json()
        if not resp_json.get("ok"):
            logger.error(f"Error uploading file to slack. Response: {resp_json}")
            return {
                "indirect": {
                    "text": f"Hubo un error al generar tu sticker en Slack: {resp_json.get('error', 'error desconocido')}. Revisa los permisos del bot."
                },
                "direct": "",
            }

        logger.info("Sticker uploaded successfully")
        # Register usage after successful upload
        phrase_service.register_sticker_usage(phrase)
    except Exception as e:
        # Log the error, maybe return a message to the user
        logger.exception(f"Exception uploading file to slack: {e}")
        return {
            "indirect": {
                "text": "Hubo un error al generar tu sticker. Inténtalo de nuevo más tarde."
            },
            "direct": "",
        }

    return {"direct": ""}  # Return an empty 200 OK
