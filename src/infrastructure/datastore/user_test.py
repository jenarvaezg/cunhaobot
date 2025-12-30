from unittest.mock import MagicMock
import pytest
from models.user import User, InlineUser
from infrastructure.datastore.user import (
    UserDatastoreRepository,
    InlineUserDatastoreRepository,
)


def create_mock_entity(data, kind="User", entity_id=None):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get
    m.__contains__.side_effect = data.__contains__
    m.keys.side_effect = data.keys
    m.values.side_effect = data.values
    m.items.side_effect = data.items
    m.key.name = entity_id or data.get("chat_id") or data.get("user_id")
    m.key.kind = kind
    m.key.id = entity_id or data.get("chat_id") or data.get("user_id")
    return m


class TestUserRepository:
    @pytest.fixture
    def repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        return UserDatastoreRepository()

    def test_entity_to_domain_user(self, repo):
        data = {"chat_id": 123, "name": "Test User", "is_group": True, "gdpr": False}
        entity = create_mock_entity(data)
        user = repo._entity_to_domain(entity)
        assert user.chat_id == 123
        assert user.name == "Test User"
        assert user.is_group is True
        assert user.gdpr is False

    def test_load_user(self, repo, mock_datastore_client):
        data = {"chat_id": 123, "name": "Test User", "is_group": False}
        entity = create_mock_entity(data, kind="User", entity_id=123)
        mock_datastore_client.get.return_value = entity

        user = repo.load(123)
        assert user is not None
        assert user.chat_id == 123
        mock_datastore_client.get.assert_called_once_with(repo.get_key(123))

        mock_datastore_client.reset_mock()
        mock_datastore_client.get.return_value = None
        user = repo.load(999)
        assert user is None

    def test_load_all_users(self, repo, mock_datastore_client):
        mock_query = MagicMock()
        mock_datastore_client.query.return_value = mock_query

        user1_data = {"chat_id": 1, "name": "User 1", "gdpr": False}
        user2_data = {"chat_id": 2, "name": "User 2", "gdpr": True}
        entity1 = create_mock_entity(user1_data)
        entity2 = create_mock_entity(user2_data)
        mock_query.fetch.return_value = [entity1, entity2]

        users = repo.load_all()
        assert len(users) == 1
        assert users[0].chat_id == 1
        assert users[0].gdpr is False

        users_ignore_gdpr = repo.load_all(ignore_gdpr=True)
        assert len(users_ignore_gdpr) == 2
        assert {u.chat_id for u in users_ignore_gdpr} == {1, 2}

    def test_save_user(self, repo, mock_datastore_client):
        user = User(chat_id=123, name="Test", is_group=False)
        repo.save(user)
        mock_datastore_client.put.assert_called_once()


class TestInlineUserRepository:
    @pytest.fixture
    def repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        return InlineUserDatastoreRepository()

    def test_entity_to_domain_inline_user(self, repo):
        data = {"user_id": 456, "name": "IUser", "usages": 5}
        entity = create_mock_entity(data)
        user = repo._entity_to_domain(entity)
        assert user.user_id == 456
        assert user.name == "IUser"
        assert user.usages == 5

    def test_load_inline_user(self, repo, mock_datastore_client):
        data = {"user_id": 456, "name": "IUser", "usages": 5}
        entity = create_mock_entity(data, kind="InlineUser", entity_id=456)
        mock_datastore_client.get.return_value = entity

        user = repo.load(456)
        assert user is not None
        assert user.user_id == 456
        mock_datastore_client.get.assert_called_once_with(repo.get_key(456))

        mock_datastore_client.reset_mock()
        mock_datastore_client.get.return_value = None
        user = repo.load(999)
        assert user is None

    def test_load_all_inline_users(self, repo, mock_datastore_client):
        mock_query = MagicMock()
        mock_datastore_client.query.return_value = mock_query

        user1_data = {"user_id": 1, "name": "IUser 1"}
        entity1 = create_mock_entity(user1_data)
        mock_query.fetch.return_value = [entity1]

        users = repo.load_all()
        assert len(users) == 1
        assert users[0].user_id == 1

    def test_save_inline_user(self, repo, mock_datastore_client):
        user = InlineUser(user_id=123, name="IUser")
        repo.save(user)
        mock_datastore_client.put.assert_called_once()
