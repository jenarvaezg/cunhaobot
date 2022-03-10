from typing import Optional

from .phrase import handle_phrase

command_router = {"/cuñao": handle_phrase}


def handle_slash(slack_data: dict) -> Optional[dict]:
    handler = command_router.get(slack_data["command"])
    if handler:
        return handler(slack_data)
