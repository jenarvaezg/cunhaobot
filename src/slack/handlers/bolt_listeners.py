import logging
import random
import urllib.parse
from typing import Any

from slack_bolt.async_app import AsyncApp

from core.config import config
from services import phrase_service, cunhao_agent, user_service
from slack.attachments import (
    build_phrase_attachments,
    build_saludo_attachments,
    build_sticker_attachments,
)

logger = logging.getLogger(__name__)


async def _register_slack_user(body: dict[str, Any], client: Any):
    try:
        user_id = None
        user_name = "Unknown"
        username = None

        if "user_id" in body:  # Command
            user_id = body["user_id"]
            user_name = body.get("user_name", "Unknown")
        elif "user" in body:  # Action
            user_data = body["user"]
            if isinstance(user_data, dict):
                user_id = user_data.get("id")
                user_name = user_data.get("name", "Unknown")
                username = user_data.get("username")
            else:
                user_id = user_data
        elif "event" in body:  # Event
            user_id = body["event"].get("user")

        if user_id and (user_name == "Unknown" or not username):
            # Fetch more info if we only have the ID
            user_info = await client.users_info(user=user_id)
            if user_info.get("ok"):
                slack_user = user_info.get("user", {})
                user_name = (
                    slack_user.get("real_name") or slack_user.get("name") or user_name
                )
                username = slack_user.get("name")

        if user_id:
            user_service.update_or_create_slack_user(
                slack_user_id=user_id,
                name=user_name,
                username=username,
            )
    except Exception as e:
        logger.error(f"Error registering slack user: {e}")


def register_listeners(app: AsyncApp):
    @app.command("/saludo")
    @app.command("/que_pasa")
    async def handle_saludo_command(
        ack: Any, body: dict[str, Any], respond: Any, client: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        text: str = body.get("text", "").strip()

        if text == "help":
            await respond(
                "Usando /saludo <texto> te doy un saludo de cuñao basado en el texto. "
                "Si no pones nada, te daré uno al azar."
            )
            return

        phrases = phrase_service.get_phrases(search=text, long=False)
        if not phrases:
            await respond(
                f'No tengo ningún saludo que encaje con la búsqueda "{text}".'
            )
            return

        phrase = random.choice(phrases)
        attachments = build_saludo_attachments(phrase.text, search=text)
        await respond(attachments=attachments)

    @app.command("/sticker")
    async def handle_sticker_command(
        ack: Any, body: dict[str, Any], respond: Any, client: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        text: str = body.get("text", "").strip()

        if text == "help":
            await respond(
                "Usando /sticker <texto> te doy un sticker de cuñao basado en el texto. "
                "Si no pones nada, te daré uno al azar."
            )
            return

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

        if selected_phrase.key:
            encoded_key = urllib.parse.quote(selected_phrase.key)
            sticker_url = f"{config.base_url}/phrase/{encoded_key}/sticker.png"
        else:
            encoded_text = urllib.parse.quote(selected_phrase.text)
            sticker_url = f"{config.base_url}/sticker/text.png?text={encoded_text}"

        attachments = build_sticker_attachments(selected_phrase.text, text, sticker_url)
        await respond(attachments=attachments)

    @app.command("/cuñao")
    async def handle_cunao_command(
        ack: Any, body: dict[str, Any], respond: Any, client: Any
    ):
        await ack()
        await _register_slack_user(body, client)
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

    @app.action("phrase")
    async def handle_choice_action(
        ack: Any, body: dict[str, Any], respond: Any, client: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        actions: list[dict[str, Any]] = body.get("actions", [])
        if not actions:
            return

        action = actions[0]
        value: str = action.get("value", "")
        user_name: str = body["user"]["name"]

        if value.startswith("send-sticker-"):
            text: str = value[len("send-sticker-") :]
            # We need to find the phrase to get the key and build the URL again
            # or we could have passed the URL in the value, but it might be too long.
            # Let's search for the exact text.
            phrases = phrase_service.get_phrases(search=text, long=True)
            # Find exact match
            selected_phrase = next((p for p in phrases if p.text == text), None)

            if not selected_phrase:
                # If not found (unlikely), generate ad-hoc
                encoded_text = urllib.parse.quote(text)
                sticker_url = f"{config.base_url}/sticker/text.png?text={encoded_text}"
            else:
                encoded_key = urllib.parse.quote(selected_phrase.key)
                sticker_url = f"{config.base_url}/phrase/{encoded_key}/sticker.png"
                phrase_service.register_sticker_usage(selected_phrase)

            await respond(
                delete_original=True,
                response_type="in_channel",
                text=f"Sticker enviado por <@{user_name}>",
                blocks=[
                    {
                        "type": "image",
                        "title": {"type": "plain_text", "text": text},
                        "image_url": sticker_url,
                        "alt_text": text,
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Enviado por <@{user_name}>",
                            }
                        ],
                    },
                ],
            )
        elif value.startswith("send-saludo-"):
            text: str = value[len("send-saludo-") :]
            full_text = f"¿Qué pasa, {text}?"
            await respond(
                delete_original=True,
                response_type="in_channel",
                text=full_text,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{full_text}*"},
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Saludo de <@{user_name}>",
                            }
                        ],
                    },
                ],
            )
        elif value.startswith("send-"):
            text: str = value[len("send-") :]
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
        elif value.startswith("shuffle-sticker-"):
            search: str = value[len("shuffle-sticker-") :]
            phrases = phrase_service.get_phrases(search=search, long=True)
            if not phrases:
                # Fallback to random if search yields nothing now
                selected_phrase = phrase_service.get_random(long=True)
            else:
                selected_phrase = random.choice(phrases)

            if selected_phrase.key:
                encoded_key = urllib.parse.quote(selected_phrase.key)
                sticker_url = f"{config.base_url}/phrase/{encoded_key}/sticker.png"
            else:
                encoded_text = urllib.parse.quote(selected_phrase.text)
                sticker_url = f"{config.base_url}/sticker/text.png?text={encoded_text}"

            attachments = build_sticker_attachments(
                selected_phrase.text, search, sticker_url
            )
            await respond(
                replace_original=True,
                response_type="ephemeral",
                attachments=attachments,
            )
        elif value.startswith("shuffle-saludo-"):
            search: str = value[len("shuffle-saludo-") :]
            phrases = phrase_service.get_phrases(search=search, long=False)
            if not phrases:
                await respond(delete_original=True)
                return

            new_phrase = random.choice(phrases)
            attachments = build_saludo_attachments(new_phrase.text, search)
            await respond(
                replace_original=True,
                response_type="ephemeral",
                attachments=attachments,
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

    @app.event("app_mention")
    async def handle_app_mention(ack: Any, body: dict[str, Any], say: Any, client: Any):
        await ack()
        await _register_slack_user(body, client)
        event = body["event"]
        text = event.get("text", "")
        response = await cunhao_agent.answer(text)
        await say(response, thread_ts=event.get("ts"))

    @app.event("message")
    async def handle_message_event(
        ack: Any, body: dict[str, Any], say: Any, client: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        event = body["event"]
        channel_type = event.get("channel_type")
        # Only handle DMs here, avoid double replying in channels (handled by app_mention)
        if channel_type == "im" and "subtype" not in event:
            text = event.get("text", "")
            response = await cunhao_agent.answer(text)
            await say(response)
