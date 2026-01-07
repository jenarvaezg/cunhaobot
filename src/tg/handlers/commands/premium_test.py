import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime


@pytest.mark.asyncio
async def test_handle_premium_active():
    with patch("tg.handlers.commands.premium.services") as mock_services:
        from tg.handlers.commands.premium import handle_premium

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
        mock_services.chat_repo.load = AsyncMock(return_value=chat)

        await handle_premium(update, context)

        update.effective_message.reply_text.assert_called_once()
        args, _ = update.effective_message.reply_text.call_args
        assert "Este chat es PREMIUM" in args[0]
        assert "01/01/2026" in args[0]


@pytest.mark.asyncio
async def test_handle_premium_not_active():
    with patch("tg.handlers.commands.premium.services") as mock_services:
        from tg.handlers.commands.premium import handle_premium

        update = MagicMock()
        update.effective_user.id = 123
        update.effective_user.name = "Test"
        update.effective_user.username = "test"
        update.effective_message.chat_id = 456
        update.effective_message.reply_invoice = AsyncMock()
        update.to_dict.return_value = {}
        context = MagicMock()

        mock_services.chat_repo.load = AsyncMock(return_value=None)

        await handle_premium(update, context)

        update.effective_message.reply_invoice.assert_called_once()
        _, kwargs = update.effective_message.reply_invoice.call_args
        assert kwargs["title"] == "Suscripción Mensual Cuñao Premium"
        assert kwargs["currency"] == "XTR"
        assert "subs_month_456" in kwargs["payload"]
