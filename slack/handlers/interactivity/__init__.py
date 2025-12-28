from .phrase import handle_phrase as handle_phrase

command_router = {"phrase": handle_phrase}


def handle_interactivity(slack_data: dict) -> dict | None:
    handler = command_router.get(slack_data["callback_id"])
    if handler:
        return handler(slack_data)
    return None
