from telegram import Update
from telegram.ext import CallbackContext
from core.container import services
from models.usage import ActionType
from tg.decorators import log_update
from tg.utils.badges import notify_new_badges


@log_update
async def handle_link(update: Update, context: CallbackContext) -> None:
    if not (message := update.effective_message) or not (user := update.effective_user):
        return

    # Log usage
    new_badges = await services.usage_service.log_usage(
        user_id=user.id,
        platform="telegram",
        action=ActionType.COMMAND,
        metadata={"command": "link"},
    )
    await notify_new_badges(update, context, new_badges)

    args = context.args
    if not args:
        # Generate Token
        token = await services.user_service.generate_link_token(user.id, "telegram")
        await message.reply_text(
            f"🔗 *Vincular Cuenta*\n\n"
            f"Tu código de vinculación es: `{token}`\n\n"
            f"Copia este código y úsalo en tu otra cuenta (Telegram o Slack) con el comando:\n"
            f"`/link {token}`\n\n"
            f"⚠️ *Atención*: La cuenta donde introduzcas el código será la *PRINCIPAL*. "
            f"La cuenta actual (donde generaste este código) se fusionará con ella y desaparecerá.",
            parse_mode="Markdown",
        )
    else:
        # Consume Token
        token = args[0].strip().upper()
        success = await services.user_service.complete_link(token, user.id, "telegram")
        if success:
            await message.reply_text(
                "✅ *Cuentas Vinculadas con Éxito*\n\n"
                "Has absorbido los poderes de tu otra cuenta. Tus puntos, medallas y frases ahora están unificados aquí.",
                parse_mode="Markdown",
            )
        else:
            await message.reply_text(
                "❌ *Error al Vincular*\n\n"
                "El código es inválido, ha expirado o intentas vincularte contigo mismo.",
                parse_mode="Markdown",
            )
