import pytest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from telegram import Update, Message, User, SuccessfulPayment
from tg.handlers.payments.checkout import handle_successful_payment
from models.gift import GiftType


@pytest.mark.asyncio
async def test_handle_successful_payment_gift_success():
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
    # Payload format: gift:chat_id:receiver_id:gift_type
    payment.invoice_payload = "gift:100:200:carajillo"
    payment.telegram_payment_charge_id = "charge_id"
    message.successful_payment = payment

    user = MagicMock(spec=User)
    user.id = 123
    user.first_name = "Sender"
    message.from_user = user

    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.refund_star_payment = AsyncMock()
    context.bot.get_chat_member = AsyncMock()

    receiver_user = MagicMock()
    receiver_user.username = "receiver"
    receiver_user.name = "Receiver"

    with (
        patch("infrastructure.datastore.gift.gift_repository.save", new_callable=AsyncMock) as mock_save_gift,
        patch("infrastructure.datastore.user.user_repository.load", new_callable=AsyncMock) as mock_load_user,
        patch("tg.handlers.payments.checkout.usage_service.log_usage", new_callable=AsyncMock) as mock_log_usage,
        patch("tg.handlers.payments.checkout.notify_new_badges", new_callable=AsyncMock),
        patch("builtins.open", new_callable=mock_open, read_data=b"image_data") as mock_file,
    ):
        mock_load_user.return_value = receiver_user
        mock_log_usage.return_value = [] # no badges

        await handle_successful_payment(update, context)

        # Verify gift saved
        mock_save_gift.assert_called_once()
        gift = mock_save_gift.call_args[0][0]
        assert gift.gift_type == GiftType.CARAJILLO
        assert gift.sender_id == 123
        assert gift.receiver_id == 200

        # Verify image sent
        mock_file.assert_called_with("src/static/gifts/carajillo.png", "rb")
        context.bot.send_photo.assert_called_once()
        assert context.bot.send_photo.call_args[1]["chat_id"] == 100
        assert context.bot.send_photo.call_args[1]["photo"].read() == b"image_data"
        
        # Verify usage logged
        assert mock_log_usage.call_count == 2 # Sender and Receiver

@pytest.mark.asyncio
async def test_handle_successful_payment_gift_image_error_fallback():
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
    payment.invoice_payload = "gift:100:200:palillo"
    payment.telegram_payment_charge_id = "charge_id"
    message.successful_payment = payment

    user = MagicMock(spec=User)
    user.id = 123
    user.first_name = "Sender"
    message.from_user = user

    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.get_chat_member = AsyncMock()

    receiver_user = MagicMock()
    receiver_user.username = "receiver"

    with (
        patch("infrastructure.datastore.gift.gift_repository.save", new_callable=AsyncMock),
        patch("infrastructure.datastore.user.user_repository.load", new_callable=AsyncMock) as mock_load_user,
        patch("tg.handlers.payments.checkout.usage_service.log_usage", new_callable=AsyncMock) as mock_log_usage,
        patch("tg.handlers.payments.checkout.notify_new_badges", new_callable=AsyncMock),
        patch("builtins.open", side_effect=FileNotFoundError("No file")),
    ):
        mock_load_user.return_value = receiver_user
        mock_log_usage.return_value = []

        await handle_successful_payment(update, context)

        # Verify fallback to text
        context.bot.send_photo.assert_not_called()
        context.bot.send_message.assert_called()
        
        # Check that send_message was called with the caption
        call_args = context.bot.send_message.call_args[1]
        assert "Toma ya" in call_args["text"] # New text has "Toma ya"