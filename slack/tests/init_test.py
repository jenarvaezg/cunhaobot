from unittest.mock import patch
from slack.handlers import handle_slack


class TestSlackInit:
    def test_handle_slack_slash(self):
        with patch(
            "slack.handlers.handle_slash", return_value="slash_res"
        ) as mock_slash:
            res = handle_slack({"command": "/test"})
            assert res == "slash_res"
            mock_slash.assert_called_once()

    def test_handle_slack_interactive(self):
        with patch(
            "slack.handlers.handle_interactivity", return_value="inter_res"
        ) as mock_inter:
            res = handle_slack({"type": "interactive_message"})
            assert res == "inter_res"
            mock_inter.assert_called_once()

    def test_handle_slack_none(self):
        assert handle_slack({}) is None

    def test_handle_slash_unknown(self):
        from slack.handlers.slash_commands import handle_slash

        assert handle_slash({"command": "/unknown"}) is None

    def test_handle_interactivity_unknown_action(self):
        from slack.handlers.interactivity.phrase import handle_phrase

        slack_data = {"actions": [{"value": "unknown-val"}]}
        assert handle_phrase(slack_data) is None
