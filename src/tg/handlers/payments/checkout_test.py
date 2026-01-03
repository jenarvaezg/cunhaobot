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

    with patch("tg.handlers.payments.checkout.poster_request_repo") as mock_repo:
        mock_repo.load = AsyncMock(return_value=None)
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
    payment.invoice_payload = "uuid-payload"
    payment.telegram_payment_charge_id = "charge_id"
    message.successful_payment = payment

    user = MagicMock(spec=User)
    user.id = 123
    user.first_name = "Pepe"
    message.from_user = user

    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.delete_message = AsyncMock()

    processing_msg = MagicMock()
    processing_msg.delete = AsyncMock()
    context.bot.send_message.return_value = processing_msg

    mock_request = MagicMock()
    mock_request.phrase = "phrase"
    mock_request.chat_id = 999
    mock_request.message_id = 888

    with (
        patch(
            "services.ai_service.ai_service.generate_image", new_callable=AsyncMock
        ) as mock_gen,
        patch("tg.handlers.payments.checkout.poster_request_repo") as mock_repo,
        patch("tg.handlers.payments.checkout.storage_service") as mock_storage,
        patch("tg.handlers.payments.checkout.badge_service") as mock_badge_service,
        patch("tg.handlers.payments.checkout.usage_service") as mock_usage_service,
        patch(
            "tg.handlers.payments.checkout.notify_new_badges", new_callable=AsyncMock
        ) as mock_notify,
    ):
        mock_gen.return_value = b"image_bytes"
        mock_repo.load = AsyncMock(return_value=mock_request)
        mock_storage.upload_bytes = AsyncMock(return_value="http://gcs/image.png")
        mock_badge_service.check_badges = AsyncMock(return_value=[])
        mock_usage_service.log_usage = AsyncMock()
        mock_repo.save = AsyncMock()

        await handle_successful_payment(update, context)

        mock_gen.assert_called_once_with("phrase")
        mock_storage.upload_bytes.assert_called_once()
        mock_repo.save.assert_called_once()
        assert mock_request.status == "completed"
        assert mock_request.image_url == "http://gcs/image.png"

        context.bot.send_photo.assert_called_once()
        # Verify it sent to the stored chat_id
        assert context.bot.send_photo.call_args[1]["chat_id"] == 999

        processing_msg.delete.assert_called_once()
        context.bot.delete_message.assert_called_once_with(chat_id=999, message_id=888)

        mock_badge_service.check_badges.assert_called_once()
        mock_usage_service.log_usage.assert_called_once()
        mock_notify.assert_called_once()


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
    payment.invoice_payload = "uuid-payload"
    payment.telegram_payment_charge_id = "charge_id"
    message.successful_payment = payment

    user = MagicMock(spec=User)
    user.id = 123
    user.first_name = "Pepe"
    message.from_user = user

    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_chat_action = AsyncMock()
    context.bot.refund_star_payment = AsyncMock()

    processing_msg = MagicMock()
    processing_msg.edit_text = AsyncMock()
    context.bot.send_message.return_value = processing_msg

    mock_request = MagicMock()
    mock_request.phrase = "phrase"
    mock_request.chat_id = 999
    mock_request.message_id = 888

    with (
        patch(
            "services.ai_service.ai_service.generate_image", new_callable=AsyncMock
        ) as mock_gen,
        patch("tg.handlers.payments.checkout.poster_request_repo") as mock_repo,
    ):
        mock_gen.side_effect = Exception("AI Error")
        mock_repo.load = AsyncMock(return_value=mock_request)
        mock_repo.save = AsyncMock()

        await handle_successful_payment(update, context)

        mock_repo.save.assert_called_once()
        assert mock_request.status == "failed"

        context.bot.refund_star_payment.assert_called_once_with(
            user_id=123, telegram_payment_charge_id="charge_id"
        )
        # Verify messages sent to stored chat_id
        assert context.bot.send_message.call_args_list[0].kwargs["chat_id"] == 999
