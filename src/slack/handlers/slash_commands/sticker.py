from services.phrase_service import PhraseService
from utils.image_utils import generate_png
from slack_sdk.web.client import WebClient


def handle_sticker(
    slack_data: dict, phrase_service: PhraseService, slack_client: WebClient
) -> dict:
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
        slack_client.files_upload_v2(
            channel=slack_data["channel_id"],
            content=sticker_image.getvalue(),
            filename="sticker.png",
            initial_comment=f'Aquí tienes tu sticker con la frase: "{phrase.text}"',
        )
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
