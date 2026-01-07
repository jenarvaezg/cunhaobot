SHORT_MODE_WORDS = ["short", "corto", "corta", "saludo"]
LONG_MODE_WORDS = ["long", "largo", "larga", "frase"]
AUDIO_MODE_WORDS = ["audio", "sonido", "sound"]
STICKER_MODE_WORDS = [
    "stickers",
    "sticker",
]
JUEGO_MODE_WORDS = ["juego", "play", "game", "jugar"]
SHORT_MODE = "SHORT"
LONG_MODE = "LONG"
AUDIO_MODE = "AUDIO"
STICKER_MODE = "STICKER"
JUEGO_MODE = "JUEGO"


def get_query_mode(query: str) -> tuple[str, str]:
    match query.strip().split():
        case []:
            return SHORT_MODE, ""
        case [first, *rest] if first in SHORT_MODE_WORDS:
            return SHORT_MODE, " ".join(rest)
        case [first, *rest] if first.isnumeric():
            return SHORT_MODE, " ".join([first] + rest)
        case [first, *rest] if first in AUDIO_MODE_WORDS:
            return AUDIO_MODE, " ".join(rest)
        case [first, *rest] if first in STICKER_MODE_WORDS:
            return STICKER_MODE, " ".join(rest)
        case [first, *rest] if first in JUEGO_MODE_WORDS:
            return JUEGO_MODE, " ".join(rest)
        case [first, *rest] if first in LONG_MODE_WORDS:
            return LONG_MODE, " ".join(rest)
        case [first, *rest]:
            return LONG_MODE, " ".join([first] + rest)
        case _:
            return SHORT_MODE, ""
