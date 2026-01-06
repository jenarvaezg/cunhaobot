import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tg.handlers.messages.photo import photo_roast


@pytest.mark.asyncio
async def test_photo_roast_private_success():
    # Setup mocks
    update = MagicMock()
    update.message.photo = [MagicMock()]
    update.message.message_id = 123

    update.effective_message = update.message
    update.effective_chat.type = "private"
    update.effective_chat.title = "Test Chat"
    update.effective_chat.username = "testchat"
    update.message.chat.type = "private"
    update.message.chat.title = "Test Chat"
    update.message.chat.username = "testchat"
    update.message.chat_id = 456
    update.effective_user.id = 456
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.message.reply_voice = AsyncMock()

    mock_file = AsyncMock()
    mock_file.download_as_bytearray.return_value = bytearray(b"fake_image")
    update.message.photo[-1].get_file = AsyncMock(return_value=mock_file)

    context = MagicMock()

    with patch("tg.handlers.messages.photo.services") as mock_services:
        mock_chat = MagicMock()
        mock_chat.is_premium = True
        mock_services.chat_repo.load = AsyncMock(return_value=mock_chat)
        mock_services.ai_service.analyze_image = AsyncMock(
            return_value="Eso está mal alicatao"
        )
        mock_services.tts_service.generate_audio = MagicMock(return_value=b"fake_audio")
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])
        mock_services.user_service.update_or_create_user = AsyncMock()

        with patch("tg.handlers.messages.photo.notify_new_badges") as mock_notify:
            await photo_roast(update, context)

            mock_services.ai_service.analyze_image.assert_called_once_with(
                b"fake_image"
            )
            mock_services.tts_service.generate_audio.assert_called_once_with(
                "Eso está mal alicatao"
            )
            mock_services.usage_service.log_usage.assert_called_once()
            mock_notify.assert_called_once()
            update.message.reply_voice.assert_called_once_with(
                voice=b"fake_audio",
                caption="Eso está mal alicatao",
                reply_to_message_id=123,
            )


@pytest.mark.asyncio
async def test_photo_roast_group_mentioned_success():
    # Setup mocks
    update = MagicMock()
    update.message.photo = [MagicMock()]
    update.message.caption = "Mira esto @TestBot"
    update.message.message_id = 123

    update.effective_message = update.message
    update.effective_chat.type = "group"
    update.effective_chat.title = "Test Group"
    update.effective_chat.username = "testgroup"
    update.message.chat.type = "group"
    update.message.chat.title = "Test Group"
    update.message.chat.username = "testgroup"
    update.message.chat_id = 789
    update.effective_user.id = 456
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.message.reply_voice = AsyncMock()

    mock_file = AsyncMock()
    mock_file.download_as_bytearray.return_value = bytearray(b"fake_image")
    update.message.photo[-1].get_file = AsyncMock(return_value=mock_file)

    context = MagicMock()
    context.bot.username = "TestBot"

    with patch("tg.handlers.messages.photo.services") as mock_services:
        mock_chat = MagicMock()
        mock_chat.is_premium = True
        mock_services.chat_repo.load = AsyncMock(return_value=mock_chat)
        mock_services.ai_service.analyze_image = AsyncMock(
            return_value="Eso está mal alicatao"
        )
        mock_services.tts_service.generate_audio = MagicMock(return_value=b"fake_audio")
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])
        mock_services.user_service.update_or_create_user = AsyncMock()

        with patch("tg.handlers.messages.photo.notify_new_badges"):
            await photo_roast(update, context)

            mock_services.ai_service.analyze_image.assert_called_once_with(
                b"fake_image"
            )
            update.message.reply_voice.assert_called_once()


@pytest.mark.asyncio
async def test_photo_roast_group_not_mentioned_ignored():
    update = MagicMock()
    update.effective_message = update.message
    update.effective_chat.type = "group"
    update.effective_chat.title = "Test Group"
    update.effective_chat.username = "testgroup"
    update.message.chat.type = "group"
    update.message.chat.title = "Test Group"
    update.message.chat.username = "testgroup"
    update.message.chat_id = 789
    update.message.photo = [MagicMock()]
    update.message.caption = "Una foto normal"
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_user.id = 456

    context = MagicMock()
    context.bot.username = "TestBot"

    await photo_roast(update, context)

    # Should return early
    update.message.photo[-1].get_file.assert_not_called()


@pytest.mark.asyncio
async def test_photo_roast_error():
    update = MagicMock()
    update.effective_message = update.message
    update.message.photo = [MagicMock()]
    update.effective_chat.type = "private"
    update.effective_chat.title = "Test Chat"
    update.effective_chat.username = "testchat"
    update.message.chat.type = "private"
    update.message.chat.title = "Test Chat"
    update.message.chat.username = "testchat"
    update.message.chat_id = 456
    update.message.reply_text = AsyncMock()
    update.effective_user.name = "Test User"
    update.effective_user.username = "testuser"
    update.effective_user.id = 456

    # Mock error
    update.message.photo[-1].get_file = AsyncMock(
        side_effect=Exception("Download failed")
    )

    with patch("tg.handlers.messages.photo.services") as mock_services:
        mock_chat = MagicMock()
        mock_chat.is_premium = True
        mock_services.chat_repo.load = AsyncMock(return_value=mock_chat)
        mock_services.user_service.update_or_create_user = AsyncMock()

        await photo_roast(update, MagicMock())

    update.message.reply_text.assert_called_once_with(
        "Mira, eso es una chapuza tan grande que no me deja ni ver la foto."
    )
