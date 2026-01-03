from telegram import Update, constants
from telegram.ext import CallbackContext
from tg.decorators import log_update
from services import usage_service, phrase_service
from models.usage import ActionType
from tg.utils.badges import notify_new_badges


@log_update
async def handle_help(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message):
        return

    new_badges = await usage_service.log_usage(
        user_id=message.from_user.id if message.from_user else "unknown",
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "help"},
    )
    await notify_new_badges(update, context, new_badges)

    p1 = (await phrase_service.get_random(long=False)).text
    p2 = (await phrase_service.get_random(long=False)).text

    text = (
        f"¿Perdido, {p1}? No te preocupes, que aquí te lo explico yo en un momento, que esto no tiene ciencia.\n\n"
        "📜 **Guía de Supervivencia:**\n\n"
        "1️⃣ **Consultoría IA y Cuñao Vision:**\n"
        "• Háblame o mencióname para recibir mi sabiduría.\n"
        "• Envíame una foto (o responde a una con una mención) para que te diga lo que opino de ella (Cuñao Vision).\n\n"
        "2️⃣ **Uso en cualquier chat (Modo Inline):**\n"
        "Escribe `@cunhaobot` en cualquier chat para buscar frases. Puedes filtrar escribiendo:\n"
        "• `@cunhaobot` -> Frases aleatorias o búsqueda de texto.\n"
        "• `@cunhaobot sticker` -> Busca stickers.\n"
        "• `@cunhaobot audio` -> Busca audios.\n\n"
        "3️⃣ **Comandos:**\n"
        "• `/poster <frase>` - Inmortaliza una frase en un póster generado por IA (50 Stars).\n"
        f"• `/perfil` - Mira tus puntos y tus medallas de {p2}.\n"
        "• `/link` - Vincula tus cuentas de Telegram y Slack.\n"
        "• `/proponer <palabra>` - Envía apelativos nuevos.\n"
        "• `/proponerfrase <frase>` - Envía frases nuevas.\n\n"
        '_"Escucha a tu cuñao, que sabe de lo que habla."_'
    )

    await message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)
