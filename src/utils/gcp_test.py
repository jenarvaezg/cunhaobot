import unittest
from unittest.mock import MagicMock, patch

from utils import gcp


class TestGCP(unittest.TestCase):
    @patch("utils.gcp.get_bucket")
    def test_get_audio_url_exists(self, mock_get_bucket):
        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.public_url = "http://example.com/audio.ogg"

        url = gcp.get_audio_url("test_file")

        mock_bucket.blob.assert_called_with("audios/test_file.ogg")
        self.assertEqual(url, "http://example.com/audio.ogg")

    @patch("utils.gcp.get_bucket")
    def test_get_audio_url_not_exists(self, mock_get_bucket):
        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False

        url = gcp.get_audio_url("test_file")

        self.assertEqual(url, "")
