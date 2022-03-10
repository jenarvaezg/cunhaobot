from typing import Optional

from .slash_commands import handle_slash
from .interactivity import handle_interactivity


def handle_slack(slack_data: dict) -> Optional[dict]:
    if "command" in slack_data:
        return handle_slash(slack_data)

    if "type" in slack_data and slack_data["type"] == "interactive_message":
        return handle_interactivity(slack_data)
