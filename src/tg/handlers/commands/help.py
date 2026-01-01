from telegram import Update, constants
from telegram.ext import CallbackContext
from tg.decorators import log_update
from services import usage_service, phrase_service
from models.usage import ActionType


@log_update
async def handle_help(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    await usage_service.log_usage(
        user_id=message.from_user.id if message.from_user else "unknown",
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "help"},
    )

    p1 = phrase_service.get_random(long=False).text
    p2 = phrase_service.get_random(long=False).text
    p3 = phrase_service.get_random(long=False).text

    text = (
        f"¿Perdido, {p1}? No te preocupes, que aquí te lo explico yo en un momento, que esto no tiene ciencia.\n\n"
        "📜 **Guía de Supervivencia:**\n\n"
        "1️⃣ **Frases y Saludos:**\n"
        "• `/cuñao [búsqueda]` - Frase aleatoria o filtrada por texto.\n"
        "• `/saludo [nombre]` - Envía un saludo personalizado.\n"
        "• `/sticker [búsqueda]` - Envía un sticker con frase.\n\n"
        "2️⃣ **Tu Progreso:**\n"
        f"• `/perfil` - Mira tus puntos y tus medallas de {p2}.\n\n"
        "3️⃣ **Aporta tu Sabiduría:**\n"
        "• `/proponer <palabra>` - Envía apelativos nuevos.\n"
        "• `/proponerfrase <frase>` - Envía frases nuevas para que las aprobemos.\n\n"
        "4️⃣ **Uso en otros chats:**\n"
        f"Escribe `@cunhaobot` seguido de lo que quieras buscar, {p3}. Puedes filtrar por `audio` o `sticker` (ej: `@cunhaobot audio {p2}`).\n\n"
        "5️⃣ **Consultoría IA:**\n"
        "Si me mencionas o me escribes por privado, te responderé con la autoridad que me dan mis años de experiencia.\n\n"
        '_"Escucha a tu cuñao, que sabe de lo que habla."_'
    )

    await message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)
