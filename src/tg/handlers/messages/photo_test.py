import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tg.handlers.messages.photo import photo_roast


@pytest.mark.asyncio
async def test_photo_roast_private_success():
    # Setup mocks
    update = MagicMock()
    update.message.photo = [MagicMock()]
    update.message.message_id = 123
    update.effective_chat.type = "private"
    update.effective_user.id = 456
    update.message.reply_voice = AsyncMock()

    # Mock get_file().download_as_bytearray()
    mock_file = AsyncMock()
    mock_file.download_as_bytearray.return_value = bytearray(b"fake_image")
    update.message.photo[-1].get_file = AsyncMock(return_value=mock_file)

    context = MagicMock()

    with (
        patch(
            "tg.handlers.messages.photo.ai_service.analyze_image",
            new_callable=AsyncMock,
        ) as mock_analyze,
        patch(
            "tg.handlers.messages.photo.tts_service.generate_audio",
            return_value=b"fake_audio",
        ) as mock_tts,
    ):
        mock_analyze.return_value = "Eso está mal alicatao"

        await photo_roast(update, context)

        mock_analyze.assert_called_once_with(b"fake_image")
        mock_tts.assert_called_once_with("Eso está mal alicatao")
        update.message.reply_voice.assert_called_once_with(
            voice=b"fake_audio",
            caption="Eso está mal alicatao",
            reply_to_message_id=123,
        )


@pytest.mark.asyncio
async def test_photo_roast_group_ignored():
    update = MagicMock()
    update.effective_chat.type = "group"
    update.message.photo = [MagicMock()]

    await photo_roast(update, MagicMock())

    # Should return early
    update.message.photo[-1].get_file.assert_not_called()


@pytest.mark.asyncio
async def test_photo_roast_error():
    update = MagicMock()
    update.message.photo = [MagicMock()]
    update.effective_chat.type = "private"
    update.message.reply_text = AsyncMock()

    # Mock error
    update.message.photo[-1].get_file = AsyncMock(
        side_effect=Exception("Download failed")
    )

    await photo_roast(update, MagicMock())

    update.message.reply_text.assert_called_once_with(
        "Mira, eso es una chapuza tan grande que no me deja ni ver la foto."
    )
