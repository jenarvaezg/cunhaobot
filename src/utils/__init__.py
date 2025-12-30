import random
from collections.abc import Iterable
from copy import deepcopy

from .security import verify_telegram_auth as verify_telegram_auth
from .text import (
    improve_punctuation as improve_punctuation,
    normalize_str as normalize_str,
)
from .ui import get_thumb as get_thumb, thumbs as thumbs


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
