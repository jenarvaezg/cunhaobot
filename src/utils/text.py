import unicodedata


def normalize_str(s: str, remove_punctuation: bool = True) -> str:
    """Returns a version of s without accents or specials characters such as ñ and lower-cased"""
    without_accents = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    if remove_punctuation:
        without_puntuations = "".join([i for i in without_accents if i.isalpha()])
        return without_puntuations.lower()
    return without_accents.lower()


def improve_punctuation(s: str) -> str:
    """Returns a version of s capitalized if the first character is a letter and a trailling dot if neccesary"""
    if not s:
        return s

    if s[0].isalpha():
        s = s[0].upper() + s[1:]
    elif len(s) > 1:
        s = s[0] + s[1].upper() + s[2:]

    if s[-1].isalpha():
        s += "."

    return s
