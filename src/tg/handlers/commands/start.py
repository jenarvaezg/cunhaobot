from telegram import Update, constants
from telegram.ext import CallbackContext
from tg.decorators import log_update
from core.container import services
from models.usage import ActionType
from tg.utils.badges import notify_new_badges


@log_update
async def handle_start(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    new_badges = await services.usage_service.log_usage(
        user_id=message.from_user.id if message.from_user else "unknown",
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "start"},
    )
    await notify_new_badges(update, context, new_badges)

    phrase_service = services.phrase_service
    p1 = (await phrase_service.get_random(long=False)).text
    p2 = (await phrase_service.get_random(long=False)).text
    p3 = (await phrase_service.get_random(long=False)).text
    p4 = (await phrase_service.get_random(long=False)).text

    text = f"""¡Qué pasa, {p1}! Bienvenido a **CuñaoBot**, el sistema de soporte a la toma de decisiones basado en el sentido común y la sabiduría de barra de bar.

Aquí tienes lo que puedo hacer por ti, {p2}:

🚀 **Comandos Directos:**
• `/cuñao [búsqueda]` - Te suelto una perla de sabiduría.
• `/sticker [búsqueda]` - Para cerrar debates con un sticker mítico.
• `/saludo [nombre]` - Saludo a tus conocidos como auténticos profesionales.
• `/perfil` - Mira tus puntos y medallas ganadas a pulso, {p3}.

✍️ **Colabora con el Bar:**
• `/proponer <palabra>` - Propón un nuevo apelativo ({p1}, {p2}...).
• `/proponerfrase <frase>` - Propón una frase épica para la posteridad.

💡 **Modo Invisible (Inline):**
Escribe `@cunhaobot` en **cualquier chat** para enviarle una frase a quien la necesite. Prueba también con `@cunhaobot audio` o `@cunhaobot sticker`, {p4}.

🤖 **Sabiduría IA:**
Háblame por privado o mencióname en un grupo y mi IA entrenada en arreglar el país te dará la solución a cualquier problema (tecnología, política o mecánica).

_"Eso con un par de martillazos se arregla, te lo digo yo."_"""

    await message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)
