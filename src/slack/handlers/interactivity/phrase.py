import random

from models.phrase import LongPhrase
from slack.attachments import build_phrase_attachments


def _handle_send(slack_data: dict) -> dict:
    value = slack_data["actions"][0]["value"]
    text = "-".join(value.split("-")[1:])
    return {
        "direct": "",
        "indirect": {
            "delete_original": True,
            "response_type": "in_channel",
            "attachments": [
                {
                    "pretext": text,
                    "title": f"Mensaje patrocinado por <@{slack_data['user']['name']}>",
                    "fallback": f"Mensaje patrocinado por <@{slack_data['user']['name']}>",
                    "actions": [],
                }
            ],
        },
    }


def _handle_shuffle(slack_data: dict) -> dict:
    value = slack_data["actions"][0]["value"]
    search = "-".join(value.split("-")[1:])
    new_phrase = random.choice(LongPhrase.get_phrases(search=search))
    return {
        "indirect": "",
        "direct": {
            "replace_original": True,
            "response_type": "ephemeral",
            "attachments": build_phrase_attachments(new_phrase.text, search),
        },
    }


def _handle_cancel(slack_data: dict) -> dict:
    return {
        "direct": {
            "delete_original": True,
        },
        "indirect": "",
    }


command_router = {
    "send": _handle_send,
    "shuffle": _handle_shuffle,
    "cancel": _handle_cancel,
}


def handle_phrase(slack_data: dict) -> dict | None:
    actions = slack_data["actions"]
    action = actions[0]
    value, *_ = action["value"].split("-")
    handler = command_router.get(value)
    if handler:
        return handler(slack_data)

    return None
