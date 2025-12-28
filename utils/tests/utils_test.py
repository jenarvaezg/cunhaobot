from utils import (
    remove_empty_from_dict,
    normalize_str,
    improve_punctuation,
    get_thumb,
    random_combination,
)


class TestUtils:
    def test_remove_empty_from_dict(self):
        d = {"a": 1, "b": None, "c": [], "d": {"e": 2, "f": ""}, "g": [1, None]}
        clean = remove_empty_from_dict(d)
        assert "b" not in clean
        assert "c" not in clean
        assert clean["g"] == [1]
        assert clean["d"] == {"e": 2}

    def test_normalize_str_no_punctuation(self):
        s = "¡Hola, mundo!"
        res = normalize_str(s, remove_punctuation=False)
        assert res == "¡hola, mundo!"

    def test_improve_punctuation_non_alpha_start(self):
        s = "¿hola"
        res = improve_punctuation(s)
        assert res == "¿Hola."

    def test_get_thumb(self):
        assert get_thumb().startswith("http")

    def test_random_combination(self):
        res = random_combination([1, 2, 3, 4, 5], 2)
        assert len(res) == 2
        assert set(res).issubset({1, 2, 3, 4, 5})
