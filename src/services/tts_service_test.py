import pytest
from unittest.mock import MagicMock, patch
from services.tts_service import TTSService
from models.phrase import Phrase


class TestTTSService:
    @pytest.fixture
    def service(self):
        self.mock_bucket = MagicMock()
        with patch(
            "services.tts_service.texttospeech.TextToSpeechClient"
        ) as mock_client:
            service = TTSService(bucket=self.mock_bucket)
            # Manually set the client to the mock to avoid triggering property
            service._client = mock_client.return_value
            return service

    def test_generate_audio(self, service):
        mock_response = MagicMock()
        mock_response.audio_content = b"fake audio"
        service.client.synthesize_speech.return_value = mock_response

        content = service.generate_audio("Hola cuñao")

        assert content == b"fake audio"
        service.client.synthesize_speech.assert_called_once()
        # Check if punctuation was improved (trailing dot added by improve_punctuation)
        call_args = service.client.synthesize_speech.call_args
        assert call_args.kwargs["request"]["input"].text == "Hola cuñao."

    def test_get_audio_url_exists(self, service):
        p = Phrase(text="test", id=123)
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_blob.public_url = "http://fake/test.ogg"
        self.mock_bucket.blob.return_value = mock_blob

        url = service.get_audio_url(p, "short")
        assert url == "http://fake/test.ogg"
        self.mock_bucket.blob.assert_called_with("audios/short-123.ogg")

    def test_get_audio_url_generate(self, service):
        p = Phrase(text="test", id=123)
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_blob.public_url = "http://fake/test.ogg"
        self.mock_bucket.blob.return_value = mock_blob

        with (
            patch.object(service, "generate_audio", return_value=b"audio data"),
        ):
            url = service.get_audio_url(p, "short")
            assert url == "http://fake/test.ogg"
            self.mock_bucket.blob.assert_called_with("audios/short-123.ogg")
            mock_blob.upload_from_string.assert_called_once_with(
                b"audio data", content_type="audio/ogg"
            )
            mock_blob.make_public.assert_called_once()
