from typing import Any
from .phrase import handle_phrase

command_router = {"/cuñao": handle_phrase}


def handle_slash(slack_data: dict, phrase_service: Any = None) -> dict | None:
    handler = command_router.get(slack_data["command"])
    if handler:
        return handler(slack_data, phrase_service=phrase_service)

    return None
