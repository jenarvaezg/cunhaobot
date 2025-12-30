import unittest
from unittest.mock import MagicMock, patch

from slack.handlers import handle_slack


class TestSlackHandlers(unittest.TestCase):
    def setUp(self):
        self.mock_phrase_service = MagicMock()
        self.mock_phrase = MagicMock()
        self.mock_phrase.text = "random phrase"
        self.mock_phrase_service.get_random.return_value = self.mock_phrase
        self.mock_phrase_service.get_phrases.return_value = []

    def test_handle_slash_help(self):
        data = {"command": "/cuñao", "text": "help"}
        resp = handle_slack(data, phrase_service=self.mock_phrase_service)
        self.assertIn("text", resp)
        self.assertIn("Usando /cuñao", resp["text"])

    def test_handle_slash_search_found(self):
        p1 = MagicMock()
        p1.text = "found phrase"
        self.mock_phrase_service.get_phrases.return_value = [p1]

        data = {"command": "/cuñao", "text": "search"}

        with patch(
            "slack.handlers.slash_commands.phrase.build_phrase_attachments"
        ) as mock_build:
            mock_build.return_value = [{"foo": "bar"}]

            resp = handle_slack(data, phrase_service=self.mock_phrase_service)

            self.assertEqual(resp["direct"], "")
            self.assertIn("attachments", resp["indirect"])
            self.mock_phrase_service.get_phrases.assert_called_with(
                search="search", long=True
            )

    def test_handle_slash_search_not_found(self):
        self.mock_phrase_service.get_phrases.return_value = []

        data = {"command": "/cuñao", "text": "notfound"}

        resp = handle_slack(data, phrase_service=self.mock_phrase_service)

        self.assertIn("No tengo ninguna frase", resp["indirect"]["text"])
