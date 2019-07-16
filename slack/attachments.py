from typing import List


def build_phrase_attachments(text: str, search: str) -> List[dict]:
    return [{
            'text': text,
            'callback_id': 'phrase',
            'actions': [{
                "name": "choice",
                "text": "Enviar",
                "type": "button",
                "value": f"send-{text}",
                'style': 'primary'
            }, {
                "name": "choice",
                "text": "Otra",
                "type": "button",
                "value": f"shuffle-{search}",
            }, {
                "name": "choice",
                "text": "Cancelar",
                "type": "button",
                "value": "cancel",
                'style': 'danger'
            }]
    }]
