from utils import (
    remove_empty_from_dict,
    normalize_str,
    improve_punctuation,
    get_thumb,
    random_combination,
    verify_telegram_auth,
)


class TestUtils:
    def test_verify_telegram_auth_no_hash(self):
        assert verify_telegram_auth({}, "token") is False

    def test_verify_telegram_auth_success(self):
        # Example from Telegram docs (roughly)
        data = {
            "id": "123",
            "first_name": "Test",
            "username": "testuser",
            "auth_date": "123456789",
        }
        import hashlib
        import hmac

        token = "secret_token"
        secret_key = hashlib.sha256(token.encode()).digest()
        data_check_arr = [f"{k}={v}" for k, v in sorted(data.items())]
        data_check_string = "\n".join(data_check_arr)
        hash_value = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        data_with_hash = data.copy()
        data_with_hash["hash"] = hash_value

        assert verify_telegram_auth(data_with_hash, token) is True

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
