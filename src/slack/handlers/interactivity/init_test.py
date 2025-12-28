import slack.handlers.interactivity


class TestInteractivityInit:
    def test_handle_interactivity_phrase(self):
        slack_data = {"callback_id": "phrase", "actions": [{"value": "cancel"}]}
        res = slack.handlers.interactivity.handle_interactivity(slack_data)
        assert res["direct"]["delete_original"] is True

    def test_handle_interactivity_unknown(self):
        assert (
            slack.handlers.interactivity.handle_interactivity(
                {"callback_id": "unknown"}
            )
            is None
        )
