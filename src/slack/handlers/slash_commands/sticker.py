import requests
from services.phrase_service import PhraseService
from utils.image_utils import generate_png
from core.config import config


def handle_sticker(slack_data: dict, phrase_service: PhraseService) -> dict:
    text = slack_data["text"]

    if text:
        phrases = phrase_service.get_phrases(search=text, long=True)
        if not phrases:
            # Try fuzzy search if no exact contains match
            phrase, score = phrase_service.find_most_similar(text, long=True)
            if score < 60:  # Threshold for similarity
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
        return {
            "indirect": {"text": "No hay frases disponibles en este momento."},
            "direct": "",
        }

    sticker_image = generate_png(phrase.text)

    try:
        # Use requests to upload the file to Slack
        response = requests.post(
            "https://slack.com/api/files.upload",
            params={
                "token": config.slack_bot_token,
                "channels": slack_data["channel_id"],
                "initial_comment": f'Aquí tienes tu sticker con la frase: "{phrase.text}"',
            },
            files={"file": ("sticker.png", sticker_image.getvalue(), "image/png")},
            timeout=10,
        )
        if not response.json().get("ok"):
            print(f"Error uploading file to slack: {response.json()}")
            return {
                "indirect": {
                    "text": "Hubo un error al generar tu sticker en Slack. Revisa los permisos del bot."
                },
                "direct": "",
            }

        # Register usage after successful upload
        phrase_service.register_sticker_usage(phrase)
    except Exception as e:
        # Log the error, maybe return a message to the user
        print(f"Error uploading file to slack: {e}")
        return {
            "indirect": {
                "text": "Hubo un error al generar tu sticker. Inténtalo de nuevo más tarde."
            },
            "direct": "",
        }

    return {"direct": ""}  # Return an empty 200 OK
