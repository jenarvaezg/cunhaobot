import unittest
from unittest.mock import MagicMock

from utils import gcp


class TestGCP(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        gcp.storage_client.reset_mock()
        gcp.bucket.reset_mock()

    def test_upload_audio(self):
        mock_blob = MagicMock()
        gcp.bucket.blob.return_value = mock_blob
        mock_blob.public_url = "http://example.com/audio.ogg"

        url = gcp.upload_audio("content", "test_file")

        gcp.bucket.blob.assert_called_with("audios/test_file.ogg")
        mock_blob.upload_from_string.assert_called_with("content")
        mock_blob.make_public.assert_called()
        self.assertEqual(url, "http://example.com/audio.ogg")

    def test_get_audio_url_exists(self):
        mock_blob = MagicMock()
        gcp.bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.public_url = "http://example.com/audio.ogg"

        url = gcp.get_audio_url("test_file")

        gcp.bucket.blob.assert_called_with("audios/test_file.ogg")
        self.assertEqual(url, "http://example.com/audio.ogg")

    def test_get_audio_url_not_exists(self):
        mock_blob = MagicMock()
        gcp.bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False

        url = gcp.get_audio_url("test_file")

        self.assertEqual(url, "")
