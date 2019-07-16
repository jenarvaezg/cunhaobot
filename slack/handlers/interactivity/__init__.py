from typing import Optional

from .phrase import handle_phrase

command_router = {
    'phrase': handle_phrase
}


def handle_interactivity(slack_data: dict) -> Optional[dict]:
    handler = command_router.get(slack_data['callback_id'])
    if handler:
        return handler(slack_data)
    return None
