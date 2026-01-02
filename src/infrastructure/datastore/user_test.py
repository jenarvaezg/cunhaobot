from unittest.mock import MagicMock
import pytest
from models.user import User
from infrastructure.datastore.user import (
    UserDatastoreRepository,
)


def create_mock_entity(data, kind="User", entity_id=None):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get
    m.__contains__.side_effect = data.__contains__
    m.keys.side_effect = data.keys
    m.values.side_effect = data.values
    m.items.side_effect = data.items
    m.key = MagicMock()
    m.key.name = (
        entity_id or data.get("id") or data.get("chat_id") or data.get("user_id")
    )
    m.key.kind = kind
    m.key.id = entity_id or data.get("id") or data.get("chat_id") or data.get("user_id")
    return m


class TestUserRepository:
    @pytest.fixture
    def repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()

        # Setup mock for client.key
        def mock_key(kind, id_):
            k = MagicMock()
            k.kind = kind
            k.id = id_
            return k

        mock_datastore_client.key.side_effect = mock_key

        # Setup mock for client.query
        def mock_query_side_effect(kind=None):
            q = MagicMock()
            q.kind = kind
            return q

        mock_datastore_client.query.side_effect = mock_query_side_effect

        return UserDatastoreRepository()

    def test_entity_to_domain_user(self, repo):
        data = {"id": 123, "name": "Test User", "gdpr": False}
        entity = create_mock_entity(data)
        user = repo._entity_to_domain(entity)
        assert user.id == 123
        assert user.name == "Test User"
        assert user.gdpr is False

    def test_entity_to_domain_compatibility(self, repo):
        # Old User kind
        data_user = {"chat_id": 123, "name": "Test User"}
        entity_user = create_mock_entity(data_user)
        user = repo._entity_to_domain(entity_user)
        assert user.id == 123

        # Old InlineUser kind
        data_inline = {"user_id": 456, "name": "Inline User"}
        entity_inline = create_mock_entity(data_inline)
        user_inline = repo._entity_to_domain(entity_inline)
        assert user_inline.id == 456

    def test_entity_to_domain_platform(self, repo):
        # New entity with platform
        data_slack = {"id": "U123", "name": "Slack User", "platform": "slack"}
        entity_slack = create_mock_entity(data_slack)
        user_slack = repo._entity_to_domain(entity_slack)
        assert user_slack.id == "U123"
        assert user_slack.platform == "slack"

        # Old entity without platform
        data_old = {"id": 123, "name": "Old User"}
        entity_old = create_mock_entity(data_old)
        user_old = repo._entity_to_domain(entity_old)
        assert user_old.platform == "telegram"

    def test_load_user(self, repo, mock_datastore_client):
        data = {"id": 123, "name": "Test User"}
        entity = create_mock_entity(data, kind="User", entity_id=123)
        mock_datastore_client.get.return_value = entity

        user = repo.load(123)
        assert user is not None
        assert user.id == 123
        assert mock_datastore_client.get.called

    def test_load_compatibility_inline(self, repo, mock_datastore_client):
        # 1. Not in User kind
        # 2. Found in InlineUser kind
        def mock_get(key):
            if key.kind == "User":
                return None
            if key.kind == "InlineUser":
                return create_mock_entity(
                    {"user_id": 456, "name": "IUser"}, kind="InlineUser", entity_id=456
                )
            return None

        mock_datastore_client.get.side_effect = mock_get

        user = repo.load(456)
        assert user is not None
        assert user.id == 456
        assert mock_datastore_client.get.call_count == 2

    def test_load_all_users(self, repo, mock_datastore_client):
        user1_data = {"id": 1, "name": "User 1", "gdpr": False}
        user2_data = {"id": 2, "name": "User 2", "gdpr": True}
        entity1 = create_mock_entity(user1_data)
        entity2 = create_mock_entity(user2_data)
        entity3 = create_mock_entity(
            {"user_id": 3, "name": "User 3"}, kind="InlineUser", entity_id=3
        )

        # mock fetch to return different things for different kinds
        def mock_fetch(self_query):
            if self_query.kind == "User":
                return [entity1, entity2]
            if self_query.kind == "InlineUser":
                return [entity3]
            return []

        # We need to mock the fetch on the mock_query returned by client.query
        def mock_query_side_effect(kind=None):
            q = MagicMock()
            q.kind = kind
            q.fetch.side_effect = lambda: mock_fetch(q)
            return q

        mock_datastore_client.query.side_effect = mock_query_side_effect

        users = repo.load_all()
        # 1 (from User kind, not GDPR) + 1 (from InlineUser kind)
        assert len(users) == 2
        ids = {u.id for u in users}
        assert 1 in ids
        assert 3 in ids

        users_ignore_gdpr = repo.load_all(ignore_gdpr=True)
        assert len(users_ignore_gdpr) == 3
        assert {u.id for u in users_ignore_gdpr} == {1, 2, 3}

    def test_save_user(self, repo):
        user = User(id=123, name="Test")
        repo.save(user)
