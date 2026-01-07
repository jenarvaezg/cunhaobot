import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import Message


@pytest.mark.asyncio
async def test_handle_game_command():
    with patch("tg.handlers.commands.game.services"):
        from tg.handlers.commands.game import handle_game_command

        update = MagicMock()
        update.effective_message.chat_id = 12345
        update.effective_message.reply_text = AsyncMock()
        update.effective_user.id = 123
        update.effective_user.name = "Test"
        update.effective_user.username = "test"
        update.to_dict.return_value = {}
        context = MagicMock()
        context.bot.send_game = AsyncMock()

        await handle_game_command(update, context)

        context.bot.send_game.assert_called_once_with(
            chat_id=12345, game_short_name="palillo_cunhao"
        )


@pytest.mark.asyncio
async def test_handle_game_callback_inline():
    with patch("tg.handlers.commands.game.services"):
        from tg.handlers.commands.game import handle_game_callback

        update = MagicMock()
        update.callback_query.game_short_name = "palillo_cunhao"
        update.callback_query.from_user.id = 999
        update.callback_query.from_user.first_name = "Test User"
        update.callback_query.from_user.username = "testuser"
        update.callback_query.inline_message_id = "inline_123"
        update.callback_query.message = None
        update.callback_query.answer = AsyncMock()
        context = MagicMock()

        with patch("tg.handlers.commands.game.config") as mock_config:
            mock_config.base_url = "https://test.com"
            await handle_game_callback(update, context)

        # Check that it answers with the correct URL
        args, kwargs = update.callback_query.answer.call_args
        url = kwargs["url"]
        assert "user_id=999" in url
        assert "inline_message_id=inline_123" in url
        assert "https://test.com" in url


@pytest.mark.asyncio
async def test_handle_game_callback_chat():
    with patch("tg.handlers.commands.game.services"):
        from tg.handlers.commands.game import handle_game_callback

        update = MagicMock()
        update.callback_query.game_short_name = "palillo_cunhao"
        update.callback_query.from_user.id = 999
        update.callback_query.from_user.first_name = "Test User"
        update.callback_query.from_user.username = "testuser"
        update.callback_query.inline_message_id = None

        # Mock query.message as a Message instance
        mock_message = MagicMock(spec=Message)
        mock_message.chat_id = 444
        mock_message.message_id = 555
        update.callback_query.message = mock_message

        update.callback_query.answer = AsyncMock()
        context = MagicMock()

        with patch("tg.handlers.commands.game.config") as mock_config:
            mock_config.base_url = "https://test.com"
            await handle_game_callback(update, context)

        args, kwargs = update.callback_query.answer.call_args
        url = kwargs["url"]
        assert "user_id=999" in url
        assert "chat_id=444" in url
        assert "message_id=555" in url


@pytest.mark.asyncio
async def test_handle_top_jugones():
    with patch("tg.handlers.commands.game.services") as mock_services:
        from tg.handlers.commands.game import handle_top_jugones

        update = MagicMock()
        update.effective_message.reply_text = AsyncMock()
        update.effective_user.id = 123
        update.effective_user.name = "Test"
        update.effective_user.username = "test"
        update.to_dict.return_value = {}
        context = MagicMock()

        user1 = MagicMock()
        user1.username = "paco"
        user1.game_high_score = 1000

        user2 = MagicMock()
        user2.username = None
        user2.name = "Pepe"
        user2.game_high_score = 500

        mock_services.user_repo.load_all = AsyncMock(return_value=[user1, user2])
        await handle_top_jugones(update, context)

        update.effective_message.reply_text.assert_called_once()
        args, _ = update.effective_message.reply_text.call_args
        text = args[0]
        assert "paco" in text
        assert "1000" in text
        assert "Pepe" in text
        assert "500" in text
        assert "🏆" in text
