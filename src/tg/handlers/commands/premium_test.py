import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from tg.handlers.commands.premium import handle_premium


@pytest.mark.asyncio
async def test_handle_premium_active(mock_container):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "test"
    update.effective_message.chat_id = 456
    update.effective_message.reply_text = AsyncMock()
    update.to_dict.return_value = {}
    context = MagicMock()

    chat = MagicMock()
    chat.is_premium = True
    chat.premium_until = datetime(2026, 1, 1)
    mock_container["chat_repo"].load = AsyncMock(return_value=chat)
    mock_container["usage_service"].log_usage.return_value = []

    await handle_premium(update, context)

    # Check for at least one call (due to badges)
    assert update.effective_message.reply_text.call_count >= 1

    # Check for premium message
    call_args_list = update.effective_message.reply_text.call_args_list
    found = False
    for call_obj in call_args_list:
        args, _ = call_obj
        if "Este chat es PREMIUM" in args[0]:
            assert "01/01/2026" in args[0]
            found = True
            break
    assert found


@pytest.mark.asyncio
async def test_handle_premium_not_active(mock_container):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "test"
    update.effective_message.chat_id = 456
    update.effective_message.reply_invoice = AsyncMock()
    update.effective_message.reply_text = AsyncMock()  # For badge notifications
    update.to_dict.return_value = {}
    context = MagicMock()

    mock_container["chat_repo"].load = AsyncMock(return_value=None)
    mock_container["usage_service"].log_usage.return_value = []

    await handle_premium(update, context)

    update.effective_message.reply_invoice.assert_called_once()
    _, kwargs = update.effective_message.reply_invoice.call_args
    assert kwargs["title"] == "Suscripción Mensual Cuñao Premium"
    assert kwargs["currency"] == "XTR"
    assert "subs_month_456" in kwargs["payload"]
