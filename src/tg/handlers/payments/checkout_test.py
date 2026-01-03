import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, Message, User, PreCheckoutQuery, SuccessfulPayment
from tg.handlers.payments.checkout import handle_pre_checkout, handle_successful_payment


@pytest.mark.asyncio
async def test_handle_pre_checkout_success():
    update = MagicMock(spec=Update)
    query = MagicMock(spec=PreCheckoutQuery)
    update.pre_checkout_query = query
    query.invoice_payload = "valid payload"
    query.answer = AsyncMock()

    # Fix Pydantic warnings by providing strings
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_user.id = 123
    update.effective_message.chat_id = 123
    update.effective_message.chat.title = "Test Chat"
    update.effective_message.chat.username = "testchat"
    update.effective_message.chat.type = "private"

    context = MagicMock()

    await handle_pre_checkout(update, context)

    query.answer.assert_called_once_with(ok=True)


@pytest.mark.asyncio
async def test_handle_pre_checkout_empty_payload():
    update = MagicMock(spec=Update)
    query = MagicMock(spec=PreCheckoutQuery)
    update.pre_checkout_query = query
    query.invoice_payload = ""
    query.answer = AsyncMock()

    # Fix Pydantic warnings by providing strings
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_user.id = 123
    update.effective_message.chat_id = 123
    update.effective_message.chat.title = "Test Chat"
    update.effective_message.chat.username = "testchat"
    update.effective_message.chat.type = "private"

    context = MagicMock()

    await handle_pre_checkout(update, context)

    query.answer.assert_called_once_with(
        ok=False, error_message="Error: Payload vacío."
    )


@pytest.mark.asyncio
async def test_handle_successful_payment_success():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message

    # Fix Pydantic warnings
    update.effective_user.id = 123
    update.effective_user.name = "Pepe"
    update.effective_user.username = "pepe"
    message.chat.type = "private"
    message.chat.title = "Test Chat"
    message.chat.username = "testchat"
    message.chat_id = 123

    payment = MagicMock(spec=SuccessfulPayment)
    payment.invoice_payload = "phrase"
    payment.telegram_payment_charge_id = "charge_id"
    message.successful_payment = payment

    user = MagicMock(spec=User)
    user.id = 123
    user.first_name = "Pepe"
    message.from_user = user

    message.reply_text = AsyncMock()
    message.chat.send_action = AsyncMock()
    message.reply_photo = AsyncMock()

    invoice_msg = MagicMock()
    invoice_msg.delete = AsyncMock()
    message.reply_to_message = invoice_msg

    processing_msg = MagicMock()
    processing_msg.delete = AsyncMock()
    message.reply_text.return_value = processing_msg

    context = MagicMock()

    with patch(
        "services.ai_service.ai_service.generate_image", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = b"image_bytes"

        await handle_successful_payment(update, context)

        mock_gen.assert_called_once_with("phrase")
        message.reply_photo.assert_called_once()
        processing_msg.delete.assert_called_once()
        invoice_msg.delete.assert_called_once()


@pytest.mark.asyncio
async def test_handle_successful_payment_failure_refund():
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message

    # Fix Pydantic warnings
    update.effective_user.id = 123
    update.effective_user.name = "Pepe"
    update.effective_user.username = "pepe"
    message.chat.type = "private"
    message.chat.title = "Test Chat"
    message.chat.username = "testchat"
    message.chat_id = 123

    payment = MagicMock(spec=SuccessfulPayment)
    payment.invoice_payload = "phrase"
    payment.telegram_payment_charge_id = "charge_id"
    message.successful_payment = payment

    user = MagicMock(spec=User)
    user.id = 123
    user.first_name = "Pepe"
    message.from_user = user

    message.reply_text = AsyncMock()
    message.chat.send_action = AsyncMock()

    processing_msg = MagicMock()
    processing_msg.edit_text = AsyncMock()
    message.reply_text.return_value = processing_msg

    context = MagicMock()
    context.bot.refund_star_payment = AsyncMock()

    with patch(
        "services.ai_service.ai_service.generate_image", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.side_effect = Exception("AI Error")

        await handle_successful_payment(update, context)

        context.bot.refund_star_payment.assert_called_once_with(
            user_id=123, telegram_payment_charge_id="charge_id"
        )
        processing_msg.edit_text.assert_called_once()
