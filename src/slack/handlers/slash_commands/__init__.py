import inspect
from typing import Any
from .phrase import handle_phrase
from .sticker import handle_sticker

command_router = {"/cuñao": handle_phrase, "/sticker": handle_sticker}


def handle_slash(
    slack_data: dict, phrase_service: Any = None, slack_client: Any = None
) -> dict | None:
    handler = command_router.get(slack_data["command"])
    if not handler:
        return None

    handler_signature = inspect.signature(handler)
    handler_params = handler_signature.parameters

    kwargs = {"slack_data": slack_data}
    if "phrase_service" in handler_params:
        kwargs["phrase_service"] = phrase_service
    if "slack_client" in handler_params:
        kwargs["slack_client"] = slack_client

    return handler(**kwargs)
