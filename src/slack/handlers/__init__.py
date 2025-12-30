from typing import Any
from .interactivity import handle_interactivity
from .slash_commands import handle_slash


def handle_slack(
    slack_data: dict, phrase_service: Any = None, slack_client: Any = None
) -> dict | None:
    if "command" in slack_data:
        return handle_slash(
            slack_data, phrase_service=phrase_service, slack_client=slack_client
        )

    if "type" in slack_data and slack_data["type"] == "interactive_message":
        return handle_interactivity(
            slack_data, phrase_service=phrase_service, slack_client=slack_client
        )

    return None
