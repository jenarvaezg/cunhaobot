def build_phrase_attachments(text: str, search: str) -> list[dict]:
    return [
        {
            "text": text,
            "callback_id": "phrase",
            "actions": [
                {
                    "name": "choice",
                    "text": "Enviar",
                    "type": "button",
                    "value": f"send-{text}",
                    "style": "primary",
                },
                {
                    "name": "choice",
                    "text": "Otra",
                    "type": "button",
                    "value": f"shuffle-{search}",
                },
                {
                    "name": "choice",
                    "text": "Cancelar",
                    "type": "button",
                    "value": "cancel",
                    "style": "danger",
                },
            ],
        }
    ]


def build_sticker_attachments(text: str, search: str, sticker_url: str) -> list[dict]:
    return [
        {
            "text": f'¿Quieres enviar este sticker? "{text}"',
            "image_url": sticker_url,
            "callback_id": "phrase",
            "actions": [
                {
                    "name": "choice",
                    "text": "Enviar",
                    "type": "button",
                    "value": f"send-sticker-{text}",
                    "style": "primary",
                },
                {
                    "name": "choice",
                    "text": "Otro",
                    "type": "button",
                    "value": f"shuffle-sticker-{search}",
                },
                {
                    "name": "choice",
                    "text": "Cancelar",
                    "type": "button",
                    "value": "cancel",
                    "style": "danger",
                },
            ],
        }
    ]


def build_saludo_attachments(text: str, search: str) -> list[dict]:
    full_text = f"¿Qué pasa, {text}?"
    return [
        {
            "text": f'¿Quieres enviar este saludo? "{full_text}"',
            "callback_id": "phrase",
            "actions": [
                {
                    "name": "choice",
                    "text": "Enviar",
                    "type": "button",
                    "value": f"send-saludo-{text}",
                    "style": "primary",
                },
                {
                    "name": "choice",
                    "text": "Otro",
                    "type": "button",
                    "value": f"shuffle-saludo-{search}",
                },
                {
                    "name": "choice",
                    "text": "Cancelar",
                    "type": "button",
                    "value": "cancel",
                    "style": "danger",
                },
            ],
        }
    ]
