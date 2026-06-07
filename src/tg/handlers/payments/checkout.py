import logging
from datetime import datetime, timedelta, timezone
from telegram import Message, Update, User
from telegram.ext import CallbackContext
from telegram.error import TelegramError

from core.container import services
from models.usage import ActionType
from models.chat import Chat
from models.gift import Gift, GIFT_PRICES, GIFT_NAMES
from services.payment import (
    GiftPayment,
    InvalidPaymentPayload,
    PosterPayment,
    SubscriptionPayment,
    parse_payment_payload,
)
from tg.decorators import log_update
from tg.utils.badges import notify_new_badges

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

    await query.answer(ok=True)


@log_update
async def handle_successful_payment(update: Update, context: CallbackContext) -> None:
    """Handles a successful payment and routes to the right paid fulfillment.

    Payload parsing is delegated to ``services.payment`` so this handler only
    decides which product (Regalo, Suscripción Premium or Póster) to fulfill.
    """
    message = update.effective_message
    if not message or not message.successful_payment:
        return

    payload = message.successful_payment.invoice_payload
    charge_id = message.successful_payment.telegram_payment_charge_id
    user = message.from_user
    if not user:
        return

    try:
        parsed = parse_payment_payload(payload)
    except InvalidPaymentPayload as exc:
        logger.error(f"Unparseable payment payload {payload!r}: {exc}")
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="Hubo un error procesando el pago. Contacta con soporte.",
        )
        return

    if isinstance(parsed, GiftPayment):
        await _fulfill_gift(update, context, message, parsed, user, charge_id)
    elif isinstance(parsed, SubscriptionPayment):
        await _fulfill_subscription(update, context, message, parsed, user)
    else:
        await _fulfill_poster(update, context, message, parsed, user, charge_id)


async def _fulfill_gift(
    update: Update,
    context: CallbackContext,
    message: Message,
    gift_payment: GiftPayment,
    user: User,
    charge_id: str,
) -> None:
    """Delivers a Regalo to the receiver Perfil within the Chat."""
    receiver_id = gift_payment.receiver_id
    gift_type = gift_payment.gift_type
    target_chat_id = (
        gift_payment.chat_id if gift_payment.chat_id is not None else message.chat_id
    )

    try:
        gift = Gift(
            sender_id=user.id,
            sender_name=user.first_name,
            receiver_id=receiver_id,
            gift_type=gift_type,
            cost=GIFT_PRICES[gift_type],
        )
        await services.gift_repo.save(gift)

        # Get receiver name for the message
        receiver_user = await services.user_repo.load(receiver_id)

        receiver_display_name = "el chaval"
        if receiver_user:
            if receiver_user.username:
                receiver_display_name = f"@{receiver_user.username}"
            else:
                receiver_display_name = receiver_user.name

        # Notify sender/group
        caption = (
            f"¡Toma ya! 🎁\n\n"
            f"<b>{user.first_name}</b> le ha invitado a un <b>{GIFT_NAMES[gift_type]}</b> a {receiver_display_name}.\n"
            f"¡Eso sí que es tener clase!\n\n"
            f"<i>Consérvalo en tu /perfil como oro en paño.</i>"
        )

        image_path = f"src/static/gifts/{gift_type.value}.png"
        try:
            with open(image_path, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=target_chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML",
                )
        except Exception as e:
            logger.error(f"Error sending gift image {image_path}: {e}")
            await context.bot.send_message(
                chat_id=target_chat_id,
                text=caption,
                parse_mode="HTML",
            )

        # Check if we need to notify privately (if user is not in the group)
        if target_chat_id != receiver_id:
            should_notify_private = False
            try:
                member = await context.bot.get_chat_member(target_chat_id, receiver_id)
                if member.status in ["left", "kicked"]:
                    should_notify_private = True
            except TelegramError:
                # Likely user not in chat or chat is private/unknown to bot
                should_notify_private = True

            if should_notify_private:
                try:
                    private_caption = (
                        f"¡Sorpresa! 🎁\n\n"
                        f"<b>{user.first_name}</b> te ha enviado un <b>{GIFT_NAMES[gift_type]}</b> desde el grupo.\n"
                        f"Como no te he visto por la barra, te lo traigo aquí.\n\n"
                        f"<i>Lo tienes guardado en tu /perfil.</i>"
                    )
                    with open(image_path, "rb") as photo:
                        await context.bot.send_photo(
                            chat_id=receiver_id,
                            photo=photo,
                            caption=private_caption,
                            parse_mode="HTML",
                        )
                except Exception as e:
                    logger.warning(
                        f"Could not send private gift notification to {receiver_id}: {e}"
                    )

        # Log usage (GIFT_SENT) for sender
        new_badges_sender = await services.usage_service.log_usage(
            user_id=user.id,
            platform="telegram",
            action=ActionType.GIFT_SENT,
            metadata={"gift_type": gift_type, "receiver_id": receiver_id},
        )

        # Log usage (GIFT_RECEIVED) for receiver
        new_badges_receiver = await services.usage_service.log_usage(
            user_id=receiver_id,
            platform="telegram",
            action=ActionType.GIFT_RECEIVED,
            metadata={"gift_type": gift_type, "sender_id": user.id},
        )

        # Notify badges for sender
        await notify_new_badges(update, context, new_badges_sender)

        # Notify badges for receiver (if any)
        if new_badges_receiver:
            badge_names = ", ".join([b.name for b in new_badges_receiver])
            try:
                await context.bot.send_message(
                    chat_id=receiver_id,
                    text=f"🏅 ¡Has desbloqueado logros!: {badge_names}",
                )
            except Exception as e:
                logger.warning(
                    f"Could not notify receiver {receiver_id} of badges: {e}"
                )

    except Exception as e:
        logger.error(f"Error processing gift {gift_payment}: {e}")
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="Hubo un error entregando el regalo. Contacta con soporte.",
        )
        # Refund attempt
        try:
            await context.bot.refund_star_payment(
                user_id=user.id,
                telegram_payment_charge_id=charge_id,
            )
        except Exception as refund_error:
            logger.error(f"Failed to refund gift: {refund_error}")


async def _fulfill_subscription(
    update: Update,
    context: CallbackContext,
    message: Message,
    subscription: SubscriptionPayment,
    user: User,
) -> None:
    """Extends Suscripción Premium for the target Chat."""
    target_chat_id = subscription.target_chat_id
    try:
        chat = await services.chat_repo.load(target_chat_id)
        if not chat:
            chat = Chat(id=target_chat_id)

        now = datetime.now(timezone.utc)
        # If already premium and not expired, extend. Else start from now.
        if chat.is_premium and chat.premium_until and chat.premium_until > now:
            chat.premium_until += timedelta(days=30)
        else:
            chat.premium_until = now + timedelta(days=30)

        await services.chat_repo.save(chat)

        # Log usage for badge (El Patrón)
        new_badges = await services.usage_service.log_usage(
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

        # Notify badges
        await notify_new_badges(update, context, new_badges)

    except Exception as e:
        logger.error(f"Error activating subscription for {target_chat_id}: {e}")
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="Hubo un error activando la suscripción. Contacta con el soporte.",
        )


async def _fulfill_poster(
    update: Update,
    context: CallbackContext,
    message: Message,
    poster: PosterPayment,
    user: User,
    charge_id: str,
) -> None:
    """Generates and delivers a Póster image from cuñadil text."""
    payload = poster.payload

    # Retrieve request data
    request_data = await services.poster_request_repo.load(payload)
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

    # Notify user that we are working on it
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
        image_bytes = await services.ai_service.generate_image(phrase)

        # Upload to Storage
        filename = f"posters/{payload}.png"
        image_url = await services.storage_service.upload_bytes(image_bytes, filename)

        # Update Request Status
        if request_data:
            request_data.image_url = image_url
            request_data.status = "completed"
            await services.poster_request_repo.save(request_data)

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
        await services.usage_service.log_usage(
            user_id=user.id,
            platform="telegram",
            action=ActionType.POSTER,
            metadata={"phrase": phrase, "image_url": image_url},
        )

        # Check badges
        new_badges = await services.badge_service.check_badges(user.id, "telegram")
        await notify_new_badges(update, context, new_badges)

    except Exception as e:
        logger.error(f"Error delivering product for payment {charge_id}: {e}")
        if request_data:
            request_data.status = "failed"
            await services.poster_request_repo.save(request_data)

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
                user_id=user.id, telegram_payment_charge_id=charge_id
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
