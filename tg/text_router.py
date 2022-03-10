from typing import Tuple

SHORT_MODE_WORDS = ["short", "corto", "corta", "saludo"]
LONG_MODE_WORDS = ["long", "largo", "larga", "frase"]
AUDIO_MODE_WORDS = ["audio", "sonido", "sound"]
STICKER_MODE_WORDS = [
    "stickers",
    "sticker",
]
SHORT_MODE = "SHORT"
LONG_MODE = "LONG"
AUDIO_MODE = "AUDIO"
STICKER_MODE = "STICKER"


def get_query_mode(query: str) -> Tuple[str, str]:
    clean_query = query.strip()
    query_words = clean_query.split(" ")
    if clean_query == "" or query_words[0] in SHORT_MODE_WORDS:
        return SHORT_MODE, " ".join(query_words[1:])

    if query_words[0].isnumeric():
        return SHORT_MODE, " ".join(query_words)

    if query_words[0] in AUDIO_MODE_WORDS:
        return AUDIO_MODE, " ".join(query_words[1:])

    if query_words[0] in STICKER_MODE_WORDS:
        return STICKER_MODE, " ".join(query_words[1:])

    if query_words[0] in LONG_MODE_WORDS:
        return LONG_MODE, " ".join(query_words[1:])

    if query_words[0].isalpha():
        return LONG_MODE, " ".join(query_words[0:])

    return "", ""
