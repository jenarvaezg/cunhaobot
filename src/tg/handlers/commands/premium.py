from telegram import LabeledPrice, Update
from telegram.ext import CallbackContext

from tg.decorators import log_update
from core.container import services


@log_update
async def handle_premium(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    if not message:
        return

    chat_id = message.chat_id
    chat = await services.chat_repo.load(chat_id)

    if chat and chat.is_premium and chat.premium_until:
        # Show status
        expiry = chat.premium_until.strftime("%d/%m/%Y")
        await message.reply_text(
            f"👑 **Este chat es PREMIUM**\n\n"
            f"Tenéis barra libre de cuñadismo IA hasta el {expiry}.\n"
            "Disfrutadlo con salud.",
            parse_mode="Markdown",
        )
        return

    # Send Invoice
    title = "Suscripción Mensual Cuñao Premium"
    description = (
        "Desbloquea IA: Análisis de Sentimiento, Chat Inteligente y Cuñao Vision."
    )
    payload = f"subs_month_{chat_id}"
    provider_token = ""  # Stars
    currency = "XTR"
    price = 100
    prices = [LabeledPrice("Suscripción Mensual", price)]

    await message.reply_invoice(
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices,
        start_parameter="premium-subscription",
    )
