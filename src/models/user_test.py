import pytest
from unittest.mock import MagicMock, patch
from models.user import User, InlineUser
from telegram.constants import ChatType


def create_mock_entity(data, key_name=None):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get
    if key_name:
        m.key.name = key_name

    def setitem(key, value):
        data[key] = value

    m.__setitem__.side_effect = setitem
    m.update.side_effect = data.update
    return m


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
        # Test repo mapper
        data = {"chat_id": 123, "name": "Test User", "is_group": True, "gdpr": False}
        entity = create_mock_entity(data)

        repo = User.get_repository()
        user = repo._entity_to_domain(entity)
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
        data = {
            "chat_id": 123,
            "name": "Loaded User",
            "is_group": False,
            "gdpr": False,
        }
        e = create_mock_entity(data)
        self.mock_client.get.return_value = e

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

        # Mock repository load to return existing user
        with (
            patch.object(User.get_repository(), "load", return_value=existing_user),
            patch.object(User.get_repository(), "save") as mock_save,
        ):
            user = User.update_or_create_from_update(update)
            assert user.name == "Updated Name"
            assert not user.gdpr
            mock_save.assert_called()

    def test_update_or_create_from_update_no_message(self):
        update = MagicMock()
        update.effective_message = None
        assert User.update_or_create_from_update(update) is None

    def test_user_load_all_ignore_gdpr(self):
        data = {"chat_id": 1, "name": "U1", "is_group": False, "gdpr": False}
        e = create_mock_entity(data)
        self.mock_client.query.return_value.fetch.return_value = [e]

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
        data = {"user_id": 456, "name": "Entity User", "usages": 5}
        entity = create_mock_entity(data)
        repo = InlineUser.get_repository()
        user = repo._entity_to_domain(entity)
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

        existing_user = InlineUser(user_id=456, name="Old Name", usages=5)

        with (
            patch.object(
                InlineUser.get_repository(), "load", return_value=existing_user
            ),
            patch.object(InlineUser.get_repository(), "save") as mock_save,
        ):
            user = InlineUser.update_or_create_from_update(update)
            assert user.name == "New Name"
            mock_save.assert_called()

    def test_update_or_create_from_update_no_name_change(self):
        update = MagicMock()
        update.effective_user.id = 456
        update.effective_user.name = "Old Name"

        existing_user = InlineUser(user_id=456, name="Old Name", usages=5)

        with (
            patch.object(
                InlineUser.get_repository(), "load", return_value=existing_user
            ),
            patch.object(InlineUser.get_repository(), "save") as mock_save,
        ):
            user = InlineUser.update_or_create_from_update(update)
            assert user.name == "Old Name"
            # Logic: if name matches, we return user and do NOT save (unless changed).
            # Code:
            # if user:
            #    if user.name != update_user.name: ... save()
            #    return user
            mock_save.assert_not_called()

    def test_update_or_create_from_update_new_inline(self):
        update = MagicMock()
        update.effective_user.id = 789
        update.effective_user.name = "New User"

        with (
            patch.object(InlineUser.get_repository(), "load", return_value=None),
            patch.object(InlineUser.get_repository(), "save") as mock_save,
        ):
            user = InlineUser.update_or_create_from_update(update)
            assert user.user_id == 789
            mock_save.assert_called_once()

    def test_get_all_inline(self):
        data = {"user_id": 1, "name": "I1", "usages": 1}
        e = create_mock_entity(data)
        self.mock_client.query.return_value.fetch.return_value = [e]

        users = InlineUser.get_all()
        assert len(users) == 1
