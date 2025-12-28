import unittest
from unittest.mock import MagicMock, patch

from slack.handlers import handle_slack


class TestSlackHandlers(unittest.TestCase):
    def setUp(self):
        # Mock random phrases
        self.patcher_phrase = patch("models.phrase.Phrase.get_random_phrase")
        self.mock_get_random_phrase = self.patcher_phrase.start()
        self.mock_get_random_phrase.return_value = MagicMock(text="buddy")
        self.mock_get_random_phrase.return_value.__str__.return_value = "buddy"

        self.patcher_long_phrase = patch("models.phrase.LongPhrase.get_phrases")
        self.mock_get_phrases = self.patcher_long_phrase.start()

    def tearDown(self):
        self.patcher_phrase.stop()
        self.patcher_long_phrase.stop()

    def test_handle_slash_help(self):
        data = {"command": "/cuñao", "text": "help"}
        resp = handle_slack(data)
        self.assertIn("text", resp)
        self.assertIn("Usando /cuñao", resp["text"])

    def test_handle_slash_search_found(self):
        p1 = MagicMock(text="found phrase")
        self.mock_get_phrases.return_value = [p1]

        data = {"command": "/cuñao", "text": "search"}

        # We need to mock build_phrase_attachments too or let it run if it's pure logic
        with patch(
            "slack.handlers.slash_commands.phrase.build_phrase_attachments"
        ) as mock_build:
            mock_build.return_value = [{"foo": "bar"}]

            resp = handle_slack(data)

            self.assertEqual(resp["direct"], "")
            self.assertIn("attachments", resp["indirect"])
            self.mock_get_phrases.assert_called_with(search="search")

    def test_handle_slash_search_not_found(self):
        self.mock_get_phrases.return_value = []

        data = {"command": "/cuñao", "text": "notfound"}

        resp = handle_slack(data)

        self.assertIn("No tengo ninguna frase", resp["indirect"]["text"])
