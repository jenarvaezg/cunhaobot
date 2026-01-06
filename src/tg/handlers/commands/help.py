from telegram import Update, constants
from telegram.ext import CallbackContext
from tg.decorators import log_update
from core.container import services
from models.usage import ActionType
from tg.utils.badges import notify_new_badges


@log_update
async def handle_help(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    new_badges = await services.usage_service.log_usage(
        user_id=message.from_user.id if message.from_user else "unknown",
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "help"},
    )
    await notify_new_badges(update, context, new_badges)

    phrase_service = services.phrase_service
    p1 = (await phrase_service.get_random(long=False)).text
    p2 = (await phrase_service.get_random(long=False)).text

    text = f"""¿Perdido, {p1}? No te preocupes, que aquí te lo explico yo en un momento, que esto no tiene ciencia.

📜 **Guía de Supervivencia:**

1️⃣ **Funcionalidades PREMIUM (Requieren /premium):**
• **Consultoría IA:** Háblame o mencióname para recibir mi sabiduría.
• **Cuñao Vision:** Envíame una foto (o responde a una con una mención) para que te diga lo que opino.
• **Reacciones Inteligentes:** Reaccionaré a tus mensajes si detecto salseo.

2️⃣ **Uso en cualquier chat (Modo Inline):**
Escribe `@cunhaobot` en cualquier chat para buscar frases. Puedes filtrar escribiendo:
• `@cunhaobot` -> Frases aleatorias o búsqueda de texto.
• `@cunhaobot sticker` -> Busca stickers.
• `@cunhaobot audio` -> Busca audios.

3️⃣ **Comandos:**
• `/premium` - Suscríbete por 100 Stars/mes para desbloquear la IA.
• `/poster <frase>` - Inmortaliza una frase en un póster generado por IA (50 Stars).
• `/perfil` - Mira tus puntos y tus medallas de {p2}.
• `/link` - Vincula tus cuentas de Telegram y Slack.
• `/proponer <palabra>` - Envía apelativos nuevos.
• `/proponerfrase <frase>` - Envía frases nuevas.

_"Escucha a tu cuñao, que sabe de lo que habla."_"""

    await message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)
