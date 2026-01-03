import logging
from telegram import Update
from telegram.ext import CallbackContext

from services.ai_service import ai_service
from tg.decorators import log_update

logger = logging.getLogger(__name__)


@log_update
async def handle_pre_checkout(update: Update, context: CallbackContext) -> None:
    """Answers the PreCheckoutQuery."""
    query = update.pre_checkout_query
    if not query:
        return

    # Check if the payload is valid (we used the phrase as payload)
    if not query.invoice_payload:
        await query.answer(ok=False, error_message="Error: Payload vacío.")
        return

    # In a real app, we might check stock or other constraints here.
    # For generated images, we just approve.
    await query.answer(ok=True)


@log_update
async def handle_successful_payment(update: Update, context: CallbackContext) -> None:
    """Handles the successful payment and delivers the product (image)."""
    message = update.effective_message
    if not message or not message.successful_payment:
        return

    payload_phrase = message.successful_payment.invoice_payload
    telegram_payment_charge_id = message.successful_payment.telegram_payment_charge_id
    user = message.from_user
    if not user:
        # Should not happen in this context, but for safety
        return

    logger.info(
        f"Payment received from {user.id} ({user.first_name}): {payload_phrase}"
    )

    # Notify user that we are working on it
    processing_msg = await message.reply_text(
        "¡Pago recibido! 🤑\n"
        "Paco se está poniendo las gafas de cerca para pintar tu obra maestra...\n"
        "Espérate un momento."
    )
    await message.chat.send_action(action="upload_photo")

    try:
        image_bytes = await ai_service.generate_image(payload_phrase)

        caption = f"🎨 *{payload_phrase}*\n\nAquí tienes, chaval. Gástatelo en salud."

        await message.reply_photo(
            photo=image_bytes, caption=caption, parse_mode="Markdown"
        )

        # We can delete the "processing" message to keep chat clean
        await processing_msg.delete()

    except Exception as e:
        logger.error(
            f"Error delivering product for payment {telegram_payment_charge_id}: {e}"
        )
        await processing_msg.edit_text(
            "⚠️ Oye, ha habido un problema técnico en el taller.\n"
            "No te preocupes, te devuelvo tus Estrellas ahora mismo."
        )

        # Refund the stars
        try:
            await context.bot.refund_star_payment(
                user_id=user.id, telegram_payment_charge_id=telegram_payment_charge_id
            )
            await message.reply_text(
                "💸 Estrellas reembolsadas. Inténtalo luego si eso."
            )
        except Exception as refund_error:
            logger.error(f"Failed to refund: {refund_error}")
            await message.reply_text(
                "‼️ Y encima no he podido devolverte el dinero automáticamente. "
                "Contacta con el soporte o el dueño del bar."
            )
