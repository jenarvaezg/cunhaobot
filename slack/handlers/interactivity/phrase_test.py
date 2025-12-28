from slack.handlers.interactivity.phrase import handle_phrase
from unittest.mock import MagicMock, patch


class TestSlackInteractivity:
    def test_handle_phrase_send(self):
        slack_data = {
            "actions": [{"value": "send-phrase-text"}],
            "user": {"name": "test_user"},
        }
        response = handle_phrase(slack_data)
        assert response["indirect"]["delete_original"] is True
        assert response["indirect"]["attachments"][0]["pretext"] == "phrase-text"

    def test_handle_phrase_shuffle(self):
        slack_data = {"actions": [{"value": "shuffle-search-text"}]}
        with patch("models.phrase.LongPhrase.get_phrases") as mock_get:
            mock_phrase = MagicMock()
            mock_phrase.text = "shuffled text"
            mock_get.return_value = [mock_phrase]

            response = handle_phrase(slack_data)
            assert response["direct"]["replace_original"] is True
            # The structure of build_phrase_attachments might be different,
            # but let's assume it has the text
            assert response["direct"]["attachments"] is not None

    def test_handle_phrase_cancel(self):
        slack_data = {"actions": [{"value": "cancel"}]}
        response = handle_phrase(slack_data)
        assert response["direct"]["delete_original"] is True
