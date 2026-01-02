import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from services.story_service import StoryService


@pytest.mark.asyncio
async def test_post_random_story_no_images():
    # Setup mocks
    mock_bucket = MagicMock()
    mock_bucket.list_blobs.return_value = []

    with patch("services.story_service.get_bucket", return_value=mock_bucket):
        service = StoryService()
        bot = MagicMock()
        result = await service.post_random_story(bot)
        assert "No hay imágenes" in result


@pytest.mark.asyncio
async def test_post_random_story_success():
    # Setup mocks
    mock_blob = MagicMock()
    mock_blob.name = "generated_images/123.png"
    mock_blob.download_as_bytes.return_value = b"fake_image_data"

    mock_bucket = MagicMock()
    mock_bucket.list_blobs.return_value = [mock_blob]

    bot = MagicMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=12345))
    bot.send_photo = AsyncMock()
    bot.send_story = AsyncMock()

    mock_phrase = MagicMock()
    mock_phrase.text = "Frase de prueba"

    with (
        patch("services.story_service.get_bucket", return_value=mock_bucket),
        patch("services.phrase_service") as mock_phrase_service,
    ):
        mock_phrase_service.phrase_repo.load.return_value = mock_phrase
        mock_phrase_service.long_repo.load.return_value = None

        service = StoryService()
        result = await service.post_random_story(bot)

        assert "éxito" in result
        bot.send_photo.assert_called_once()
        bot.send_story.assert_called_once()
        # Verify caption includes part of the phrase
        args, kwargs = bot.send_story.call_args
        assert "Frase de prueba" in kwargs["caption"]
