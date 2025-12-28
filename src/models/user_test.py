import pytest
from unittest.mock import MagicMock, patch
from models.user import User, InlineUser
from telegram.constants import ChatType


class TestUser:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        self.mock_client = mock_datastore_client
        self.mock_client.reset_mock()
        self.mock_client.get.return_value = None
        yield

    def test_init(self):
        user = User(chat_id=123, name="Test User", is_group=False)
        assert user.chat_id == 123
        assert user.name == "Test User"
        assert not user.is_group
        assert not user.gdpr

    def test_from_entity(self):
        entity = {"chat_id": 123, "name": "Test User", "is_group": True, "gdpr": False}
        user = User.from_entity(entity)
        assert user.chat_id == 123
        assert user.name == "Test User"
        assert user.is_group
        assert not user.gdpr

    def test_save(self):
        user = User(chat_id=123, name="Test User", is_group=False)
        user.save()
        self.mock_client.key.assert_called_with("User", 123)
        self.mock_client.put.assert_called()

    def test_load(self):
        self.mock_client.get.return_value = {
            "chat_id": 123,
            "name": "Loaded User",
            "is_group": False,
            "gdpr": False,
        }
        user = User.load(123)
        assert user.name == "Loaded User"
        self.mock_client.key.assert_called_with("User", 123)

    def test_delete_soft(self):
        user = User(chat_id=123, name="Test User", is_group=False)
        user.delete(hard=False)
        assert user.gdpr
        self.mock_client.put.assert_called()

    def test_delete_hard(self):
        user = User(chat_id=123, name="Test User", is_group=False)
        user.delete(hard=True)
        self.mock_client.delete.assert_called()

    def test_update_or_create_from_update_new(self):
        update = MagicMock()
        update.effective_message.chat_id = 123
        update.effective_message.chat.PRIVATE = ChatType.PRIVATE
        update.effective_message.chat.type = ChatType.PRIVATE
        update.effective_message.from_user.name = "New User"

        with patch.object(User, "load", return_value=None), patch.object(User, "save"):
            user = User.update_or_create_from_update(update)
            assert user.chat_id == 123
            assert user.name == "New User"

    def test_update_or_create_from_update_existing(self):
        update = MagicMock()
        update.effective_message.chat_id = 123
        update.effective_message.chat.PRIVATE = ChatType.PRIVATE
        update.effective_message.chat.type = ChatType.PRIVATE
        update.effective_message.from_user.name = "Updated Name"

        existing_user = User(chat_id=123, name="Old Name", is_group=False, gdpr=True)

        with (
            patch.object(User, "load", return_value=existing_user),
            patch.object(User, "save"),
        ):
            user = User.update_or_create_from_update(update)
            assert user.name == "Updated Name"
            assert not user.gdpr

    def test_update_or_create_from_update_no_message(self):
        update = MagicMock()
        update.effective_message = None
        assert User.update_or_create_from_update(update) is None

    def test_user_load_all_ignore_gdpr(self):
        self.mock_client.query.return_value.fetch.return_value = [
            {"chat_id": 1, "name": "U1", "is_group": False, "gdpr": False}
        ]
        users = User.load_all(ignore_gdpr=False)
        assert len(users) == 1
        self.mock_client.query.return_value.add_filter.assert_called_with(
            "gdpr", "=", False
        )


class TestInlineUser:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        self.mock_client = mock_datastore_client
        self.mock_client.reset_mock()
        self.mock_client.get.return_value = None
        yield

    def test_init(self):
        user = InlineUser(user_id=456, name="Inline User", usages=10)
        assert user.user_id == 456
        assert user.name == "Inline User"
        assert user.usages == 10

    def test_from_entity(self):
        entity = {"user_id": 456, "name": "Entity User", "usages": 5}
        user = InlineUser.from_entity(entity)
        assert user.user_id == 456
        assert user.usages == 5

    def test_add_usage(self):
        user = InlineUser(user_id=456, name="Inline User", usages=10)
        user.add_usage()
        assert user.usages == 11
        self.mock_client.put.assert_called()

    def test_update_or_create_from_update_no_user(self):
        update = MagicMock()
        update.effective_user = None
        assert InlineUser.update_or_create_from_update(update) is None

    def test_update_or_create_from_update_name_change(self):
        update = MagicMock()
        update.effective_user.id = 456
        update.effective_user.name = "New Name"

        # provide a real dict that from_entity can use
        existing_entity = {"user_id": 456, "name": "Old Name", "usages": 5}

        # We need to mock datastore.Client() to return our mock client
        with patch("google.cloud.datastore.Client", return_value=self.mock_client):
            self.mock_client.get.return_value = existing_entity
            with patch.object(InlineUser, "save") as mock_save:
                user = InlineUser.update_or_create_from_update(update)
                assert user.name == "New Name"
                mock_save.assert_called()

    def test_update_or_create_from_update_no_name_change(self):
        update = MagicMock()
        update.effective_user.id = 456
        update.effective_user.name = "Old Name"

        existing_entity = {"user_id": 456, "name": "Old Name", "usages": 5}

        with patch("google.cloud.datastore.Client", return_value=self.mock_client):
            self.mock_client.get.return_value = existing_entity
            with patch.object(InlineUser, "save") as mock_save:
                user = InlineUser.update_or_create_from_update(update)
                assert user.name == "Old Name"
                mock_save.assert_not_called()

    def test_update_or_create_from_update_new_inline(self):
        update = MagicMock()
        update.effective_user.id = 789
        update.effective_user.name = "New User"

        with patch("google.cloud.datastore.Client", return_value=self.mock_client):
            self.mock_client.get.return_value = None
            with patch.object(InlineUser, "save") as mock_save:
                user = InlineUser.update_or_create_from_update(update)
                assert user.user_id == 789
                mock_save.assert_called_once()

    def test_get_all_inline(self):
        self.mock_client.query.return_value.fetch.return_value = [
            {"user_id": 1, "name": "I1", "usages": 1}
        ]
        users = InlineUser.get_all()
        assert len(users) == 1
