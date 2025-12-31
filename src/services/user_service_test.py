import pytest
from unittest.mock import MagicMock
from telegram.constants import ChatType
from models.user import User
from services.user_service import UserService


class TestUserService:
    @pytest.fixture
    def service(self):
        self.user_repo = MagicMock()
        return UserService(self.user_repo)

    def test_update_or_create_user_new(self, service):
        update = MagicMock()
        update.effective_message.chat_id = 123
        update.effective_message.chat.PRIVATE = ChatType.PRIVATE
        update.effective_message.chat.type = ChatType.PRIVATE
        update.effective_message.from_user.name = "New User"
        update.effective_message.from_user.username = "new_user"

        service.user_repo.load.return_value = None

        user = service.update_or_create_user(update)
        assert user.id == 123
        assert user.name == "New User"
        assert user.username == "new_user"
        service.user_repo.save.assert_called_once()

    def test_update_or_create_user_update(self, service):
        update = MagicMock()
        update.effective_message.chat_id = 123
        update.effective_message.chat.PRIVATE = ChatType.PRIVATE
        update.effective_message.chat.type = ChatType.PRIVATE
        update.effective_message.from_user.name = "Updated User"
        update.effective_message.from_user.username = "updated_user"

        existing = User(id=123, name="Old", gdpr=True)
        service.user_repo.load.return_value = existing

        user = service.update_or_create_user(update)
        assert user.name == "Updated User"
        assert user.username == "updated_user"
        assert user.gdpr is False
        service.user_repo.save.assert_called_once_with(existing)

    def test_update_or_create_user_group(self, service):
        update = MagicMock()
        update.effective_message.chat_id = 456
        update.effective_message.chat.PRIVATE = ChatType.PRIVATE
        update.effective_message.chat.type = ChatType.GROUP
        update.effective_message.chat.title = "My Group"
        update.effective_message.from_user = None

        service.user_repo.load.return_value = None

        user = service.update_or_create_user(update)
        assert user.id == 456
        assert user.name == "My Group"
        assert user.is_group is True
        assert user.username is None

    def test_update_or_create_user_no_message(self, service):
        update = MagicMock()
        update.effective_message = None
        assert service.update_or_create_user(update) is None

    def test_update_or_create_inline_user_new(self, service):
        update = MagicMock()
        update.effective_user.id = 789
        update.effective_user.name = "New Inline"
        update.effective_user.username = "new_inline"

        service.user_repo.load.return_value = None

        user = service.update_or_create_inline_user(update)
        assert user.id == 789
        assert user.username == "new_inline"
        service.user_repo.save.assert_called_once()

    def test_delete_user_hard(self, service):
        user = User(id=123)
        service.delete_user(user, hard=True)
        service.user_repo.delete.assert_called_once_with(123)

    def test_delete_user_soft(self, service):
        user = User(id=123, gdpr=False)
        service.delete_user(user, hard=False)
        assert user.gdpr is True
        service.user_repo.save.assert_called_once_with(user)

    def test_add_inline_usage(self, service):
        user = User(id=123, usages=5)
        service.add_inline_usage(user)
        assert user.usages == 6
        service.user_repo.save.assert_called_once_with(user)

    def test_add_points(self, service):
        user_id = 123
        points = 10

        user = User(id=user_id, points=5, is_group=False)
        service.user_repo.load.return_value = user

        service.add_points(user_id, points)

        assert user.points == 15
        service.user_repo.save.assert_called_once_with(user)
