import logging
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import CallbackContext

from services.ai_service import ai_service
from services import poster_request_repo, badge_service, usage_service
from models.usage import ActionType
from models.chat import Chat
from infrastructure.datastore.chat import chat_repository
from tg.decorators import log_update
from tg.utils.badges import notify_new_badges
from utils.storage import storage_service

logger = logging.getLogger(__name__)


@log_update
async def handle_pre_checkout(update: Update, context: CallbackContext) -> None:
    """Answers the PreCheckoutQuery."""
    query = update.pre_checkout_query
    if not query:
        return

    payload = query.invoice_payload
    if not payload:
        await query.answer(ok=False, error_message="Error: Payload vacío.")
        return

    if payload.startswith("subs_month_"):
        await query.answer(ok=True)
        return

    # Verify if we have the request data
    request_data = await poster_request_repo.load(payload)
    if not request_data:
        # Fallback for old payloads (plain text phrases) or lost data
        pass

    await query.answer(ok=True)


@log_update
async def handle_successful_payment(update: Update, context: CallbackContext) -> None:
    """Handles the successful payment and delivers the product (image)."""
    message = update.effective_message
    if not message or not message.successful_payment:
        return

    payload = message.successful_payment.invoice_payload
    telegram_payment_charge_id = message.successful_payment.telegram_payment_charge_id
    user = message.from_user
    if not user:
        return

    if payload.startswith("subs_month_"):
        try:
            target_chat_id = int(payload.replace("subs_month_", ""))
            chat = await chat_repository.load(target_chat_id)
            if not chat:
                chat = Chat(id=target_chat_id)

            now = datetime.now(timezone.utc)
            # If already premium and not expired, extend. Else start from now.
            if chat.is_premium and chat.premium_until and chat.premium_until > now:
                chat.premium_until += timedelta(days=30)
            else:
                chat.premium_until = now + timedelta(days=30)

            await chat_repository.save(chat)

            # Log usage for badge (El Patrón)
            # Use the user who paid, regardless of who the chat belongs to
            new_badges = await usage_service.log_usage(
                user_id=user.id,
                platform="telegram",
                action=ActionType.SUBSCRIPTION,
                metadata={"target_chat_id": target_chat_id, "amount": 100},
            )

            await context.bot.send_message(
                chat_id=target_chat_id,
                text=(
                    "¡Pago recibido! ⭐️\n"
                    "¡Sois VIPs! La barra libre de Cuñadismo IA está abierta por 30 días.\n"
                    "Disfrutad de vuestros privilegios."
                ),
            )

            # Notify badges in the chat where payment happened (likely the same)
            await notify_new_badges(update, context, new_badges)

        except Exception as e:
            logger.error(f"Error activating subscription for {payload}: {e}")
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="Hubo un error activando la suscripción. Contacta con el soporte.",
            )
        return

    # Retrieve request data
    request_data = await poster_request_repo.load(payload)
    if request_data:
        phrase = request_data.phrase
        original_chat_id = request_data.chat_id
        invoice_message_id = request_data.message_id
    else:
        # Fallback: payload is the phrase
        phrase = payload
        original_chat_id = message.chat_id
        invoice_message_id = None

    logger.info(f"Payment received from {user.id} ({user.first_name}): {phrase}")

    # Notify user that we are working on it (in the chat where payment confirmed)
    processing_msg = await context.bot.send_message(
        chat_id=original_chat_id,
        text=(
            "¡Pago recibido! 🤑\n"
            "Paco se está poniendo las gafas de cerca para pintar tu obra maestra...\n"
            "Espérate un momento."
        ),
    )

    # Delete the invoice message if we know it
    if invoice_message_id:
        try:
            await context.bot.delete_message(
                chat_id=original_chat_id, message_id=invoice_message_id
            )
        except Exception as e:
            logger.debug(f"Could not delete invoice message: {e}")

    # Send action to the target chat
    await context.bot.send_chat_action(chat_id=original_chat_id, action="upload_photo")

    try:
        image_bytes = await ai_service.generate_image(phrase)

        # Upload to Storage
        filename = f"posters/{payload}.png"
        image_url = await storage_service.upload_bytes(image_bytes, filename)

        # Update Request Status
        if request_data:
            request_data.image_url = image_url
            request_data.status = "completed"
            await poster_request_repo.save(request_data)

        caption = f"🎨 *{phrase}*\n\nAquí tienes, chaval. Gástatelo en salud."

        await context.bot.send_photo(
            chat_id=original_chat_id,
            photo=image_bytes,
            caption=caption,
            parse_mode="Markdown",
        )

        # Delete the "processing" message
        await processing_msg.delete()

        # Log usage
        await usage_service.log_usage(
            user_id=user.id,
            platform="telegram",
            action=ActionType.POSTER,
            metadata={"phrase": phrase, "image_url": image_url},
        )

        # Check badges
        new_badges = await badge_service.check_badges(user.id, "telegram")
        await notify_new_badges(update, context, new_badges)

    except Exception as e:
        logger.error(
            f"Error delivering product for payment {telegram_payment_charge_id}: {e}"
        )
        if request_data:
            request_data.status = "failed"
            await poster_request_repo.save(request_data)

        await context.bot.send_message(
            chat_id=original_chat_id,
            text=(
                "⚠️ Oye, ha habido un problema técnico en el taller.\n"
                "No te preocupes, te devuelvo tus Estrellas ahora mismo."
            ),
        )

        # Refund the stars
        try:
            await context.bot.refund_star_payment(
                user_id=user.id, telegram_payment_charge_id=telegram_payment_charge_id
            )
            await context.bot.send_message(
                chat_id=original_chat_id,
                text="💸 Estrellas reembolsadas. Inténtalo luego si eso.",
            )
        except Exception as refund_error:
            logger.error(f"Failed to refund: {refund_error}")
            await context.bot.send_message(
                chat_id=original_chat_id,
                text=(
                    "‼️ Y encima no he podido devolverte el dinero automáticamente. "
                    "Contacta con el soporte o el dueño del bar."
                ),
            )
