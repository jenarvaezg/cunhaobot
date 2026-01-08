import pytest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
from telegram import Update, Message, User, SuccessfulPayment
from telegram.error import TelegramError
from tg.handlers.payments.checkout import handle_successful_payment


@pytest.mark.asyncio
async def test_handle_successful_payment_gift_private_notification(mock_container):
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message

    # Fix Pydantic warnings
    update.effective_user.id = 123
    update.effective_user.name = "Pepe"
    update.effective_user.username = "pepe"
    message.chat.type = "group"
    message.chat.title = "Group Chat"
    message.chat_id = 100  # Group ID

    payment = MagicMock(spec=SuccessfulPayment)
    # Payload: gift:chat_id:receiver_id:gift_type
    payment.invoice_payload = "gift:100:200:carajillo"
    payment.telegram_payment_charge_id = "charge_id"
    message.successful_payment = payment

    user = MagicMock(spec=User)
    user.id = 123
    user.first_name = "Sender"
    user.username = "sender"
    message.from_user = user

    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.get_chat_member = AsyncMock()

    receiver_user = MagicMock()
    receiver_user.username = "receiver"
    receiver_user.name = "Receiver"

    context.bot.get_chat_member.side_effect = TelegramError("User not found")

    mock_container["gift_repo"].save = AsyncMock()
    mock_container["user_repo"].load = AsyncMock(return_value=receiver_user)
    mock_container["usage_service"].log_usage.return_value = []

    with (
        patch(
            "tg.handlers.payments.checkout.notify_new_badges", new_callable=AsyncMock
        ),
        patch("builtins.open", new_callable=mock_open, read_data=b"image_data"),
    ):
        await handle_successful_payment(update, context)

        # Verify public message sent to Group (100)
        assert context.bot.send_photo.call_args_list[0].kwargs["chat_id"] == 100

        # Verify private message sent to Receiver (200)
        assert context.bot.send_photo.call_args_list[1].kwargs["chat_id"] == 200
        assert (
            "Como no te he visto por la barra"
            in context.bot.send_photo.call_args_list[1].kwargs["caption"]
        )


@pytest.mark.asyncio
async def test_handle_successful_payment_gift_no_private_notification_if_present(
    mock_container,
):
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    update.effective_message = message

    # Fix Pydantic warnings
    update.effective_user.id = 123
    update.effective_user.name = "Pepe"
    update.effective_user.username = "pepe"
    message.chat.type = "group"
    message.chat.title = "Group Chat"
    message.chat_id = 100  # Group ID

    payment = MagicMock(spec=SuccessfulPayment)
    # Payload: gift:chat_id:receiver_id:gift_type
    payment.invoice_payload = "gift:100:200:carajillo"
    payment.telegram_payment_charge_id = "charge_id"
    message.successful_payment = payment

    user = MagicMock(spec=User)
    user.id = 123
    user.first_name = "Sender"
    user.username = "sender"
    message.from_user = user

    context = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.get_chat_member = AsyncMock()

    receiver_user = MagicMock()
    receiver_user.username = "receiver"
    receiver_user.name = "Receiver"

    # Simulate user IS in chat
    member = MagicMock()
    member.status = "member"
    context.bot.get_chat_member.return_value = member

    mock_container["gift_repo"].save = AsyncMock()
    mock_container["user_repo"].load = AsyncMock(return_value=receiver_user)
    mock_container["usage_service"].log_usage.return_value = []

    with (
        patch(
            "tg.handlers.payments.checkout.notify_new_badges", new_callable=AsyncMock
        ),
        patch("builtins.open", new_callable=mock_open, read_data=b"image_data"),
    ):
        await handle_successful_payment(update, context)

        # Verify ONLY public message sent to Group (100)
        assert context.bot.send_photo.call_count == 1
        assert context.bot.send_photo.call_args_list[0].kwargs["chat_id"] == 100
