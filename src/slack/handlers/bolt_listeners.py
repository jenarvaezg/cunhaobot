import logging
import random
from typing import Any

from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from services import phrase_service
from slack.attachments import build_phrase_attachments
from utils.image_utils import generate_png

logger = logging.getLogger(__name__)


def register_listeners(app: AsyncApp):
    @app.command("/sticker")
    async def handle_sticker_command(
        ack: Any, body: dict[str, Any], client: AsyncWebClient, respond: Any
    ):
        await ack()
        text: str = body.get("text", "").strip()
        channel_id: str | None = body.get("channel_id")

        logger.info(
            f"Handling sticker request for text: '{text}' in channel: {channel_id}"
        )

        if text:
            phrases = phrase_service.get_phrases(search=text, long=True)
            if not phrases:
                phrase, score = phrase_service.find_most_similar(text, long=True)
                if score < 60:
                    await respond(
                        f'No tengo ninguna frase que encaje con "{text}". ¿Querías decir algo como "{phrase.text}"?'
                    )
                    return
                else:
                    selected_phrase = phrase
            else:
                selected_phrase = random.choice(phrases)
        else:
            selected_phrase = phrase_service.get_random(long=True)

        if not selected_phrase:
            await respond("No hay frases disponibles en este momento.")
            return

        logger.info(f"Generating sticker for phrase: '{selected_phrase.text}'")
        sticker_image = generate_png(selected_phrase.text)

        try:
            logger.info(f"Uploading sticker to Slack channel {channel_id}...")

            # Use Bolt client for upload
            # files_upload_v2 is the recommended way
            await client.files_upload_v2(
                channel=channel_id,
                initial_comment=f'Aquí tienes tu sticker con la frase: "{selected_phrase.text}"',
                file=sticker_image.getvalue(),
                filename="sticker.png",
            )

            logger.info("Sticker uploaded successfully")
            phrase_service.register_sticker_usage(selected_phrase)
        except Exception as e:
            logger.exception(f"Exception uploading file to slack: {e}")
            await respond(
                "Hubo un error al generar tu sticker. Inténtalo de nuevo más tarde."
            )

    @app.command("/cuñao")
    async def handle_cunao_command(ack: Any, body: dict[str, Any], respond: Any):
        await ack()
        text: str = body.get("text", "").strip()

        if text == "help":
            random_phrase = phrase_service.get_random().text
            await respond(
                f"Usando /cuñao <texto> te doy frases de cuñao que incluyan texto en su contenido. "
                f"Si no me das texto para buscar, tendrás una frase al azar, {random_phrase}"
            )
            return

        phrases = phrase_service.get_phrases(search=text, long=True)
        if not phrases:
            random_phrase = phrase_service.get_random().text
            await respond(
                f'No tengo ninguna frase que encaje con la busqueda "{text}", {random_phrase}.'
            )
            return

        phrase = random.choice(phrases)
        attachments = build_phrase_attachments(phrase.text, search=text)
        await respond(attachments=attachments)

    @app.action("choice")
    async def handle_choice_action(ack: Any, body: dict[str, Any], respond: Any):
        await ack()
        actions: list[dict[str, Any]] = body.get("actions", [])
        if not actions:
            return

        action = actions[0]
        value: str = action.get("value", "")

        if value.startswith("send-"):
            text: str = value[len("send-") :]
            user_name: str = body["user"]["name"]
            await respond(
                delete_original=True,
                response_type="in_channel",
                attachments=[
                    {
                        "pretext": text,
                        "title": f"Mensaje patrocinado por <@{user_name}>",
                        "fallback": f"Mensaje patrocinado por <@{user_name}>",
                        "actions": [],
                    }
                ],
            )
        elif value.startswith("shuffle-"):
            search: str = value[len("shuffle-") :]
            phrases = phrase_service.get_phrases(search=search, long=True)
            if not phrases:
                await respond(delete_original=True)
                return

            new_phrase = random.choice(phrases)
            attachments = build_phrase_attachments(new_phrase.text, search)
            await respond(
                replace_original=True,
                response_type="ephemeral",
                attachments=attachments,
            )
        elif value == "cancel":
            await respond(delete_original=True)
