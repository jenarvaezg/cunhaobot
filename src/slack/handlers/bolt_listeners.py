import logging
import random
import urllib.parse
from typing import Any, Callable, cast

from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from core.config import config
from core.container import services
from models.usage import ActionType
from slack.attachments import (
    build_phrase_attachments,
    build_saludo_attachments,
    build_sticker_attachments,
)
from slack.utils import notify_new_badges_slack

logger = logging.getLogger(__name__)

EMOJI_MAP = {
    "🍺": "beer",
    "🇪🇸": "flag-es",
    "🥘": "shallow_pan_of_food",
    "🤡": "clown_face",
    "👎": "thumbsdown",
    "❤️": "heart",
    "🔥": "fire",
    "😂": "joy",
}


async def _register_slack_user(body: dict[str, Any], client: AsyncWebClient) -> None:
    try:
        user_id: str | None = None
        user_name: str = "Unknown"
        username: str | None = None

        if "user_id" in body:  # Command
            user_id = cast(str, body["user_id"])
            user_name = cast(str, body.get("user_name", "Unknown"))
        elif "user" in body:  # Action
            user_data = body["user"]
            if isinstance(user_data, dict):
                user_id = cast(str | None, user_data.get("id"))
                user_name = cast(str, user_data.get("name", "Unknown"))
                username = cast(str | None, user_data.get("username"))
            else:
                user_id = cast(str, user_data)
        elif "event" in body:  # Event
            user_id = cast(str | None, body["event"].get("user"))

        if user_id and (user_name == "Unknown" or not username):
            user_info = await client.users_info(user=user_id)
            if user_info.get("ok"):
                slack_user = cast(dict[str, Any], user_info.get("user", {}))
                user_name = cast(
                    str,
                    slack_user.get("real_name") or slack_user.get("name") or user_name,
                )
                username = cast(str | None, slack_user.get("name"))

        if user_id:
            await services.user_service.update_or_create_slack_user(
                slack_user_id=user_id,
                name=user_name,
                username=username,
            )
    except Exception as e:
        logger.error(f"Error registering slack user: {e}")


def register_listeners(app: AsyncApp) -> None:
    @app.command("/link")
    async def handle_link_command(
        ack: Callable[..., Any],
        body: dict[str, Any],
        respond: Callable[..., Any],
        client: AsyncWebClient,
    ) -> None:
        await ack()
        await _register_slack_user(body, client)
        user_id = body["user_id"]
        text = body.get("text", "").strip()

        if not text:
            token = await services.user_service.generate_link_token(user_id, "slack")
            await respond(
                f"""🔗 *Vincular Cuenta*\n\nTu código de vinculación es: `{token}`\n\nCopia este código y úsalo en tu otra cuenta (Telegram o Slack) con el comando:\n`/link {token}`\n\n⚠️ *Atención*: La cuenta donde introduzcas el código será la *PRINCIPAL*. La cuenta actual (donde generaste este código) se fusionará con ella y desaparecerá.""",
                response_type="ephemeral",
            )
        else:
            token = text.upper()
            success = await services.user_service.complete_link(token, user_id, "slack")
            if success:
                await respond(
                    """✅ *Cuentas Vinculadas con Éxito*\n\nHas absorbido los poderes de tu otra cuenta. Tus puntos, medallas y frases ahora están unificados aquí.""",
                    response_type="ephemeral",
                )
            else:
                await respond(
                    """❌ *Error al Vincular*\n\nEl código es inválido, ha expirado o intentas vincularte contigo mismo.""",
                    response_type="ephemeral",
                )

    @app.command("/saludo")
    @app.command("/que_pasa")
    async def handle_saludo_command(
        ack: Any, body: dict[str, Any], respond: Any, client: Any, say: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        text: str = body.get("text", "").strip()

        if text == "help":
            await respond(
                "Usando /saludo <texto> te doy un saludo de cuñao basado en el texto. Si no pones nada, te daré uno al azar."
            )
            return

        phrases = await services.phrase_service.get_phrases(search=text, long=False)
        if not phrases:
            await respond(
                f'No tengo ningún saludo que encaje con la búsqueda "{text}".'
            )
            return

        phrase = random.choice(phrases)
        new_badges = await services.usage_service.log_usage(
            user_id=body["user_id"],
            platform="slack",
            action=ActionType.SALUDO,
            phrase_id=phrase.id,
        )
        attachments = build_saludo_attachments(phrase.text, search=text)
        await respond(attachments=attachments)
        await notify_new_badges_slack(say, new_badges)

    @app.command("/sticker")
    async def handle_sticker_command(
        ack: Any, body: dict[str, Any], respond: Any, client: Any, say: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        text: str = body.get("text", "").strip()

        if text == "help":
            await respond(
                "Usando /sticker <texto> te doy un sticker de cuñao basado en el texto. Si no pones nada, te daré uno al azar."
            )
            return

        if text:
            phrases = await services.phrase_service.get_phrases(search=text, long=True)
            if not phrases:
                phrase, score = await services.phrase_service.find_most_similar(
                    text, long=True
                )
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
            selected_phrase = await services.phrase_service.get_random(long=True)

        if not selected_phrase:
            await respond("No hay frases disponibles en este momento.")
            return

        new_badges = await services.usage_service.log_usage(
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
        await notify_new_badges_slack(say, new_badges)

    @app.command("/cuñao")
    async def handle_cunao_command(
        ack: Any, body: dict[str, Any], respond: Any, client: Any, say: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        text: str = body.get("text", "").strip()

        if text == "help":
            random_phrase = (await services.phrase_service.get_random()).text
            await respond(
                f"Usando /cuñao <texto> te doy frases de cuñao que incluyan texto en su contenido. Si no me das texto para buscar, tendrás una frase al azar, {random_phrase}"
            )
            return

        phrases = await services.phrase_service.get_phrases(search=text, long=True)
        if not phrases:
            random_phrase = (await services.phrase_service.get_random()).text
            await respond(
                f'No tengo ninguna frase que encaje con la busqueda "{text}", {random_phrase}.'
            )
            return

        phrase = random.choice(phrases)
        new_badges = await services.usage_service.log_usage(
            user_id=body["user_id"],
            platform="slack",
            action=ActionType.PHRASE,
            phrase_id=phrase.id,
        )
        attachments = build_phrase_attachments(phrase.text, search=text)
        await respond(attachments=attachments)
        await notify_new_badges_slack(say, new_badges)

    @app.action("phrase")
    async def handle_choice_action(
        ack: Any, body: dict[str, Any], respond: Any, client: Any, say: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        actions: list[dict[str, Any]] = body.get("actions", [])
        if not actions:
            return

        action = actions[0]
        value: str = action.get("value", "")
        user_name: str = body["user"]["name"]
        user_id: str = body["user"]["id"]

        if value.startswith("send-sticker-"):
            text: str = value[len("send-sticker-") :]
            phrases = await services.phrase_service.get_phrases(search=text, long=True)
            selected_phrase = next((p for p in phrases if p.text == text), None)

            if not selected_phrase:
                encoded_text = urllib.parse.quote(text)
                sticker_url = f"{config.base_url}/sticker/text.png?text={encoded_text}"
            else:
                encoded_id = urllib.parse.quote(str(selected_phrase.id))
                sticker_url = f"{config.base_url}/phrase/{encoded_id}/sticker.png"
                await services.phrase_service.register_sticker_usage(selected_phrase)

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
            new_badges = await services.usage_service.log_usage(
                user_id=user_id, platform="slack", action=ActionType.STICKER
            )
            await notify_new_badges_slack(say, new_badges)
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
            new_badges = await services.usage_service.log_usage(
                user_id=user_id, platform="slack", action=ActionType.SALUDO
            )
            await notify_new_badges_slack(say, new_badges)
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
            phrases = await services.phrase_service.get_phrases(
                search=search, long=True
            )
            if not phrases:
                selected_phrase = await services.phrase_service.get_random(long=True)
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
            phrases = await services.phrase_service.get_phrases(
                search=search, long=False
            )
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
            phrases = await services.phrase_service.get_phrases(
                search=search, long=True
            )
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

        await services.usage_service.log_usage(
            user_id=user_id,
            platform="slack",
            action=ActionType.COMMAND,
            metadata={"command": "app_home_opened"},
        )

        try:
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
                                "text": """Soy el bot que tu espacio de trabajo no sabía que necesitaba. Estoy aquí para aportar esa dosis de sabiduría cuñadil necesaria para sobrevivir al día a día.

*Comandos disponibles:*
• `/cuñao [búsqueda]` - Suelto una perla de sabiduría.
• `/sticker [búsqueda]` - Envío un sticker con frase mítica.
• `/saludo [nombre]` - Saludo como es debido.
• `/perfil` - Mira tus estadísticas.
• `/link` - Vincula cuentas de otras plataformas.
• `/help` - Muestro esta ayuda.""",
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
        await services.usage_service.log_usage(
            user_id=body["user_id"],
            platform="slack",
            action=ActionType.COMMAND,
            metadata={"command": "help"},
        )
        p1 = (await services.phrase_service.get_random(long=False)).text
        p2 = (await services.phrase_service.get_random(long=False)).text
        p3 = (await services.phrase_service.get_random(long=False)).text
        await respond(
            f"""*Guía Rápida de Supervivencia Cuñadil:*\n\n• `/cuñao [texto]` - Busca una frase mítica que contenga ese texto.
• `/sticker [texto]` - Genera un sticker con una frase para cerrar debates.
• `/poster [frase]` - (Próximamente en Slack) Inmortaliza tu sabiduría con IA.
• `/saludo [nombre]` - Envía un saludo personalizado (ej: `/saludo {p1}`).
• `/perfil` - Mira tus puntos y medallas de {p2}.
• `/link` - Vincula tus cuentas de Telegram y Slack para unificar puntos.
• *Mención* - Si me mencionas (@CuñaoBot) te responderé con mi sabiduría IA.\n\n_"Eso con un par de martillazos se arregla, te lo digo yo, {p3}. "_"""
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

        await services.usage_service.log_usage(
            user_id=user_id,
            platform=platform,
            action=ActionType.COMMAND,
            metadata={"command": "profile"},
        )

        user = await services.user_service.get_user(user_id, platform)
        if not user:
            p = (await services.phrase_service.get_random(long=False)).text
            await respond(f"Todavía no tengo tu ficha, {p}. ¡Empieza a usar el bot!")
            return

        stats = await services.usage_service.get_user_stats(user_id, platform)
        all_badges_progress = await services.badge_service.get_all_badges_progress(
            user_id, platform
        )

        earned_elements = []
        pending_elements = []

        for p in all_badges_progress:
            badge = p.badge
            if p.is_earned:
                earned_elements.append(f"{badge.icon} *{badge.name}*")
            else:
                filled = p.progress // 10
                bar = "●" * filled + "○" * (10 - filled)
                progress_text = f"{p.progress}%"
                if p.target > 0:
                    progress_text = f"{p.current}/{p.target}"
                pending_elements.append(
                    f"{badge.icon} *{badge.name}*\n`{bar} {progress_text}`"
                )

        earned_text = (
            "\n".join(earned_elements)
            if earned_elements
            else "_Todavía no tienes medallas_"
        )
        pending_text = (
            "\n\n*🚀 Próximos logros:*" + "\n".join(pending_elements)
            if pending_elements
            else ""
        )

        await respond(
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"👤 *Perfil de {user.name}*\n━━━━━━━━━━━━━━━\n🏆 *Puntos:* {user.points}\n📊 *Usos totales:* {stats['total_usages']}\n\n🎖️ *Logros conseguidos:*\n{earned_text}{pending_text}",
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

        response = await services.cunhao_agent.answer(text)
        await services.usage_service.log_usage(
            user_id=event.get("user"),
            platform="slack",
            action=ActionType.AI_ASK,
        )
        await say(response, thread_ts=event.get("ts"))

        try:
            reaction_unicode = await services.ai_service.analyze_sentiment_and_react(
                text
            )
            if reaction_unicode and reaction_unicode in EMOJI_MAP:
                await client.reactions_add(
                    name=EMOJI_MAP[reaction_unicode],
                    channel=event.get("channel"),
                    timestamp=event.get("ts"),
                )

                reaction_badges = await services.usage_service.log_usage(
                    user_id=event.get("user"),
                    platform="slack",
                    action=ActionType.REACTION_RECEIVED,
                )
                await notify_new_badges_slack(say, reaction_badges)
        except Exception as e:
            logger.warning(f"Failed to react on Slack: {e}")

    @app.event("message")
    async def handle_message_event(
        ack: Any, body: dict[str, Any], say: Any, client: Any, context: Any
    ):
        await ack()
        await _register_slack_user(body, client)
        event = body["event"]

        if event.get("bot_id") or event.get("subtype") == "bot_message":
            return

        text = event.get("text", "")
        channel_type = event.get("channel_type")
        bot_user_id = context.get("bot_user_id")
        is_mentioned = bot_user_id and f"<@{bot_user_id}>" in text

        if channel_type == "im" and "subtype" not in event:
            response = await services.cunhao_agent.answer(text)
            await services.usage_service.log_usage(
                user_id=event.get("user"),
                platform="slack",
                action=ActionType.AI_ASK,
            )
            await say(response)

        if not is_mentioned:
            try:
                reaction_unicode = (
                    await services.ai_service.analyze_sentiment_and_react(text)
                )
                if reaction_unicode and reaction_unicode in EMOJI_MAP:
                    await client.reactions_add(
                        name=EMOJI_MAP[reaction_unicode],
                        channel=event.get("channel"),
                        timestamp=event.get("ts"),
                    )

                    reaction_badges = await services.usage_service.log_usage(
                        user_id=event.get("user"),
                        platform="slack",
                        action=ActionType.REACTION_RECEIVED,
                    )
                    await notify_new_badges_slack(say, reaction_badges)
            except Exception as e:
                if "already_reacted" not in str(e):
                    logger.warning(f"Failed to react on Slack: {e}")
