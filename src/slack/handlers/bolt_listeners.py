import logging
import random
import urllib.parse
from typing import Any

from slack_bolt.async_app import AsyncApp

from core.config import config
from services import (
    phrase_service,
    cunhao_agent,
    user_service,
    usage_service,
    badge_service,
)
from models.usage import ActionType
from slack.attachments import (
    build_phrase_attachments,
    build_saludo_attachments,
    build_sticker_attachments,
)
from slack.utils import get_slack_history

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
        await usage_service.log_usage(
            user_id=body["user_id"],
            platform="slack",
            action=ActionType.SALUDO,
            phrase_id=phrase.id,
        )
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

        await usage_service.log_usage(
            user_id=body["user_id"],
            platform="slack",
            action=ActionType.STICKER,
            phrase_id=selected_phrase.id,
        )

        if selected_phrase.id:
            encoded_id = urllib.parse.quote(str(selected_phrase.id))
            sticker_url = f"{config.base_url}/phrase/{encoded_id}/sticker.png"
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
        await usage_service.log_usage(
            user_id=body["user_id"],
            platform="slack",
            action=ActionType.PHRASE,
            phrase_id=phrase.id,
        )
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
                encoded_id = urllib.parse.quote(str(selected_phrase.id))
                sticker_url = f"{config.base_url}/phrase/{encoded_id}/sticker.png"
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

            if selected_phrase.id:
                encoded_id = urllib.parse.quote(str(selected_phrase.id))
                sticker_url = f"{config.base_url}/phrase/{encoded_id}/sticker.png"
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

    @app.event("app_home_opened")
    async def handle_app_home_opened(ack: Any, body: dict[str, Any], client: Any):
        await ack()
        await _register_slack_user(body, client)
        user_id = body["event"]["user"]

        await usage_service.log_usage(
            user_id=user_id,
            platform="slack",
            action=ActionType.COMMAND,
            metadata={"command": "app_home_opened"},
        )

        try:
            # Simple App Home view
            await client.views_publish(
                user_id=user_id,
                view={
                    "type": "home",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*¡Qué pasa, <@{user_id}>! Bienvenid@ a CuñaoBot.*",
                            },
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": (
                                    "Soy el bot que tu espacio de trabajo no sabía que necesitaba. "
                                    "Estoy aquí para aportar esa dosis de sabiduría cuñadil necesaria para sobrevivir al día a día.\n\n"
                                    "*Comandos disponibles:*\n"
                                    "• `/cuñao [búsqueda]` - Suelto una perla de sabiduría.\n"
                                    "• `/sticker [búsqueda]` - Envío un sticker con frase mítica.\n"
                                    "• `/saludo [nombre]` - Saludo como es debido.\n"
                                    "• `/help` - Muestro esta ayuda."
                                ),
                            },
                        },
                        {"type": "divider"},
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Si me mencionas en un canal o me escribes por privado, te contestaré como un auténtico profesional.",
                            },
                        },
                    ],
                },
            )
        except Exception as e:
            logger.error(f"Error publishing App Home: {e}")

    @app.command("/help")
    async def handle_help_command(ack: Any, body: dict[str, Any], respond: Any):
        await ack()
        await usage_service.log_usage(
            user_id=body["user_id"],
            platform="slack",
            action=ActionType.COMMAND,
            metadata={"command": "help"},
        )
        await respond(
            "*Guía Rápida de Supervivencia Cuñadil:*\n\n"
            "• `/cuñao [texto]` - Busca una frase mítica que contenga ese texto.\n"
            "• `/sticker [texto]` - Genera un sticker con una frase para cerrar debates.\n"
            "• `/saludo [nombre]` - Envía un saludo personalizado (ej: `/saludo máquina`).\n"
            "• `/perfil` - Mira tus puntos y medallas de fiera.\n"
            "• *Mención* - Si me mencionas (@CuñaoBot) te responderé con mi sabiduría IA.\n\n"
            '_"Eso con un par de martillazos se arregla, te lo digo yo."_'
        )

    @app.command("/perfil")
    @app.command("/profile")
    async def handle_profile_command(
        ack: Any, body: dict[str, Any], respond: Any, client: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        user_id = body["user_id"]
        platform = "slack"

        await usage_service.log_usage(
            user_id=user_id,
            platform=platform,
            action=ActionType.COMMAND,
            metadata={"command": "profile"},
        )

        user = user_service.get_user(user_id, platform)
        if not user:
            await respond("Todavía no tengo tu ficha, fiera. ¡Empieza a usar el bot!")
            return

        stats = usage_service.get_user_stats(user_id, platform)

        badges_text = ""
        if user.badges:
            badge_elements = []
            for b_id in user.badges:
                b_info = badge_service.get_badge_info(b_id)
                if b_info:
                    badge_elements.append(f"{b_info.icon} *{b_info.name}*")
            badges_text = "\n" + "\n".join(badge_elements)
        else:
            badges_text = "\n_Todavía no tienes medallas, ¡dale caña!_"

        await respond(
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"👤 *Perfil de {user.name}*\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🏆 *Puntos:* {user.points}\n"
                        f"📊 *Usos totales:* {stats['total_usages']}\n"
                        f"🎖️ *Logros:* {badges_text}",
                    },
                }
            ]
        )

    @app.event("app_mention")
    async def handle_app_mention(
        ack: Any, body: dict[str, Any], say: Any, client: Any, context: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        event = body["event"]
        text = event.get("text", "")
        thread_ts = event.get("thread_ts")
        bot_user_id = context.get("bot_user_id")

        # Extract history using API (either thread or general channel context)
        history = await get_slack_history(
            client,
            event.get("channel"),
            bot_user_id,
            thread_ts=thread_ts or event.get("ts"),
        )

        response = await cunhao_agent.answer(text, history=history)
        await usage_service.log_usage(
            user_id=event.get("user"),
            platform="slack",
            action=ActionType.AI_ASK,
        )
        await say(response, thread_ts=event.get("ts"))

    @app.event("message")
    async def handle_message_event(
        ack: Any, body: dict[str, Any], say: Any, client: Any, context: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        event = body["event"]
        channel_type = event.get("channel_type")
        # Only handle DMs here, avoid double replying in channels (handled by app_mention)
        if channel_type == "im" and "subtype" not in event:
            text = event.get("text", "")
            thread_ts = event.get("thread_ts")
            bot_user_id = context.get("bot_user_id")

            # Extract history using API
            history = await get_slack_history(
                client, event.get("channel"), bot_user_id, thread_ts=thread_ts
            )

            response = await cunhao_agent.answer(text, history=history)
            await usage_service.log_usage(
                user_id=event.get("user"),
                platform="slack",
                action=ActionType.AI_ASK,
            )
            await say(response)
