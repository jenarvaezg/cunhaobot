from telegram import Update, constants
from telegram.ext import CallbackContext
from tg.decorators import log_update
from services import usage_service, phrase_service
from models.usage import ActionType


@log_update
async def handle_start(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    await usage_service.log_usage(
        user_id=message.from_user.id if message.from_user else "unknown",
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "start"},
    )

    p1 = phrase_service.get_random().text

    text = (
        f"¡Qué pasa, {p1}! Bienvenido a **CuñaoBot**, el sistema de soporte a la toma de decisiones "
        "basado en el sentido común y la sabiduría de barra de bar.\n\n"
        "Aquí tienes lo que puedo hacer por ti, fiera:\n\n"
        "🚀 **Comandos Directos:**\n"
        "• `/cuñao [búsqueda]` - Te suelto una perla de sabiduría.\n"
        "• `/sticker [búsqueda]` - Para cerrar debates con un sticker mítico.\n"
        "• `/saludo [nombre]` - Saludo a tus conocidos como auténticos profesionales.\n"
        "• `/perfil` - Mira tus puntos y medallas ganadas a pulso.\n\n"
        "✍️ **Colabora con el Bar:**\n"
        "• `/proponer <palabra>` - Propón un nuevo apelativo (fiera, máquina...).\n"
        "• `/proponerfrase <frase>` - Propón una frase épica para la posteridad.\n\n"
        "💡 **Modo Invisible (Inline):**\n"
        "Escribe `@cunhaobot` en **cualquier chat** para enviarle una frase a quien la necesite. "
        "Prueba también con `@cunhaobot audio` o `@cunhaobot sticker`.\n\n"
        "🤖 **Sabiduría IA:**\n"
        "Háblame por privado o mencióname en un grupo y mi IA entrenada en arreglar el país te dará "
        "la solución a cualquier problema (tecnología, política o mecánica).\n\n"
        '_"Eso con un par de martillazos se arregla, te lo digo yo."_'
    )

    await message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)
