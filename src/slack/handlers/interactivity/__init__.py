from typing import Any
from .phrase import handle_phrase as handle_phrase

command_router = {"phrase": handle_phrase}


def handle_interactivity(
    slack_data: dict, phrase_service: Any = None, slack_client: Any = None
) -> dict | None:
    handler = command_router.get(slack_data["callback_id"])
    if handler:
        return handler(slack_data, phrase_service=phrase_service)
    return None
