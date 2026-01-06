import logging
from typing import TYPE_CHECKING
from google.cloud import texttospeech
from utils.text import improve_punctuation

if TYPE_CHECKING:
    from models.phrase import Phrase, LongPhrase
    from google.cloud.storage import Bucket

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self, bucket: Bucket):
        self._client: texttospeech.TextToSpeechClient | None = None
        self._bucket = bucket
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="es-ES", name="es-ES-Neural2-B"
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.OGG_OPUS
        )

    @property
    def client(self) -> texttospeech.TextToSpeechClient:
        if self._client is None:
            self._client = texttospeech.TextToSpeechClient()
        return self._client

    def generate_audio(self, text: str) -> bytes:
        """Generates audio bytes from text using Neural2."""
        # Improve text for TTS
        processed_text = improve_punctuation(text)

        input_text = texttospeech.SynthesisInput(text=processed_text)

        response = self.client.synthesize_speech(
            request={
                "input": input_text,
                "voice": self.voice,
                "audio_config": self.audio_config,
            }
        )
        return response.audio_content

    def get_audio_url(self, phrase: Phrase | LongPhrase, result_type: str) -> str:
        """Gets the audio URL, generating it if it doesn't exist."""
        if phrase.id is None:
            logger.error(f"Cannot generate audio for phrase without ID: {phrase.text}")
            return ""

        file_name = f"audios/{result_type}-{phrase.id}.ogg"
        blob = self._bucket.blob(file_name)

        if blob.exists():
            return blob.public_url

        # Generate and upload
        logger.info(f"Generating audio for: {phrase.text}")
        try:
            audio_content = self.generate_audio(phrase.text)
            blob.upload_from_string(audio_content, content_type="audio/ogg")
            try:
                blob.make_public()
            except Exception as e:
                logger.warning(
                    f"Could not make blob public (might already be public or restricted): {e}"
                )
            return blob.public_url
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return ""
