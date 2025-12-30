import hashlib
import hmac


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
