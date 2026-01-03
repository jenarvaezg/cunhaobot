from telegram import LabeledPrice, Update
from telegram.ext import CallbackContext

from tg.decorators import log_update


@log_update
async def handle_poster(update: Update, context: CallbackContext) -> None:
    """Sends an invoice to generate a poster for a phrase."""
    message = update.effective_message
    if not message:
        return

    # Extract the phrase from the command arguments
    # /poster <phrase>
    args = context.args
    if not args:
        await message.reply_text(
            "⚠️ Tienes que decirme qué frase quieres inmortalizar.\n"
            "Ejemplo: `/poster El diésel es el futuro`",
            parse_mode="Markdown",
        )
        return

    phrase = " ".join(args)

    if len(phrase) > 200:
        await message.reply_text(
            "⚠️ ¡Esa frase es más larga que un día sin pan! Resúmela un poco (máx 200 caracteres).",
        )
        return

    title = "Poster Cuñao IA"
    description = f"Generación de imagen única para: '{phrase}'"
    # Payload contains the phrase to retrieve it later upon successful payment
    payload = phrase
    provider_token = ""  # Empty for XTR (Stars)
    currency = "XTR"
    prices = [LabeledPrice("Poster IA", 1)]  # 1 Star

    await message.reply_invoice(
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices,
        start_parameter="poster-generation",
    )
