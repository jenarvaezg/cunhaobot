import hashlib
import hmac
import random
import unicodedata
from collections.abc import Iterable
from copy import deepcopy


def verify_telegram_auth(data: dict, token: str) -> bool:
    """
    Verifies the data received from the Telegram Login Widget.
    See: https://core.telegram.org/widgets/login#checking-authorization
    """
    auth_data = data.copy()
    check_hash = auth_data.pop("hash", None)
    if not check_hash:
        return False

    # 1. Sort the data by key
    data_check_arr = []
    for key, value in sorted(auth_data.items()):
        if value:
            data_check_arr.append(f"{key}={value}")

    # 2. Join with newlines
    data_check_string = "\n".join(data_check_arr)

    # 3. Calculate secret key: SHA256(token)
    secret_key = hashlib.sha256(token.encode()).digest()

    # 4. Calculate HMAC-SHA256(data_check_string, secret_key)
    hash_value = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    # 5. Compare with received hash
    return hmac.compare_digest(hash_value, check_hash)


thumbs = [
    "https://cdn.20m.es/img2/recortes/2018/02/06/632781-600-338.jpg",
    "https://i.blogs.es/c60c05/quien-javier/450_1000.jpg",
    "https://media-cdn.tripadvisor.com/media/photo-s/0f/f9/86/eb/junto-a-mi-cunado-compartiendo.jpg",
    "https://img.elcomercio.pe/files/ec_article_videogalleria/uploads/2018/06/18/5b27a6c5c9c49.jpeg",
    "https://fotos.perfil.com/2016/10/26/1026claudiominnicellig.jpg",
    "https://www.ecestaticos.com/imagestatic/clipping/7f5/900/7f59009441d3cf042f374f50756f3c5b/tu-cunado-ese-que-dice-que-escribe.jpg?mtime=1456847457",
    "https://s4.eestatic.com/2017/05/05/reportajes/entrevistas/VOX-Santiago_Abascal-Entrevistas_213740088_33819883_1024x576.jpg",
    "https://i.ytimg.com/vi/NyOwsYAPzTE/hqdefault.jpg",
    "https://pbs.twimg.com/media/DFRYYkRXgAIGOjI.jpg",
    "http://www.eluniversalqueretaro.mx/sites/default/files/styles/f03-651x400/public/2018/04/06/q8-20.jpg.jpg?itok=G2zZUM1c",
    "https://static3.elcomercio.es/www/pre2017/multimedia/noticias/201703/26/media/22940314.jpg",
    "https://www.elplural.com/uploads/s1/62/50/39/el-lider-de-vox-santiago-abascal-sin-barba_6_585x329.png",
    "https://pbs.twimg.com/media/DwA6mRuW0AAj8FX.jpg",
    "https://s2.eestatic.com/2018/12/03/actualidad/Actualidad_357976969_108513450_1024x576.jpg",
    "http://www.elboletin.com/imagenes/portada/santiago-abascal-p.jpg",
    "https://amenzing.com/wp-content/uploads/2018/12/santiago-abascal.jpg",
]


def get_thumb() -> str:
    return random.choice(thumbs)


def random_combination(iterable: Iterable, r: int) -> tuple:
    pool = tuple(iterable)
    n = len(pool)
    indices: list[int] = sorted(random.sample(range(n), r))
    return tuple(pool[i] for i in indices)


def remove_empty_from_dict(di: dict | list) -> dict | list:
    d = deepcopy(di)
    if isinstance(d, dict):
        return {
            k: remove_empty_from_dict(v)
            for k, v in d.items()
            if v and remove_empty_from_dict(v)
        }
    if isinstance(d, list):
        return [remove_empty_from_dict(v) for v in d if v and remove_empty_from_dict(v)]
    return d


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
