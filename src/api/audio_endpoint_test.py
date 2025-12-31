from unittest.mock import patch
from litestar.status_codes import HTTP_307_TEMPORARY_REDIRECT
from litestar.testing import TestClient
from main import app
from models.phrase import Phrase


def test_phrase_audio_redirect():
    p = Phrase(text="test audio", id=123)
    with (
        patch("services.phrase_repo.load", return_value=p),
        patch(
            "services.tts_service.TTSService.get_audio_url",
            return_value="http://gcs/audio.ogg",
        ),
    ):
        with TestClient(app=app) as client:
            response = client.get("/phrase/123/audio.ogg", follow_redirects=False)
            assert response.status_code == HTTP_307_TEMPORARY_REDIRECT
            assert response.headers["location"] == "http://gcs/audio.ogg"


def test_phrase_audio_not_found():
    with (
        patch("services.phrase_repo.load", return_value=None),
        patch("services.long_phrase_repo.load", return_value=None),
    ):
        with TestClient(app=app) as client:
            response = client.get("/phrase/999/audio.ogg")
            assert response.status_code == 404
