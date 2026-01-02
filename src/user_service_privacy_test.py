from unittest.mock import MagicMock
from services.user_service import UserService
from models.user import User


def test_toggle_privacy():
    user_repo = MagicMock()
    service = UserService(user_repo=user_repo)

    user = User(id="123", is_private=False)
    user_repo.load.return_value = user

    # 1. Toggle On
    result = service.toggle_privacy("123", "telegram")
    assert result is True
    assert user.is_private is True
    user_repo.save.assert_called_with(user)

    # 2. Toggle Off
    result = service.toggle_privacy("123", "telegram")
    assert result is False
    assert user.is_private is False


def test_toggle_privacy_user_not_found():
    user_repo = MagicMock()
    service = UserService(user_repo=user_repo)
    user_repo.load.return_value = None

    result = service.toggle_privacy("999", "telegram")
    assert result is None
