from unittest.mock import MagicMock
import pytest
from datetime import datetime, timezone
from models.gift import GiftType
from infrastructure.datastore.gift import GiftDatastoreRepository


def create_mock_entity(data, kind="Gift", entity_id=12345):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get

    def setitem(key, value):
        data[key] = value

    m.__setitem__.side_effect = setitem
    m.update.side_effect = data.update
    m.key.kind = kind

    if isinstance(entity_id, int):
        m.key.id = entity_id
        m.key.name = None
    else:
        m.key.name = entity_id
        m.key.id = None

    return m


class TestGiftRepository:
    @pytest.fixture
    def repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        return GiftDatastoreRepository()

    def test_entity_to_domain(self, repo):
        now = datetime.now(timezone.utc)
        data = {
            "sender_id": 1,
            "sender_name": "Sender",
            "receiver_id": 2,
            "gift_type": "carajillo",
            "created_at": now,
            "cost": 5,
        }
        entity = create_mock_entity(data)

        gift = repo._entity_to_domain(entity)
        assert gift.sender_id == 1
        assert gift.receiver_id == 2
        assert gift.gift_type == GiftType.CARAJILLO
        assert gift.cost == 5
        assert gift.created_at == now

    @pytest.mark.asyncio
    async def test_get_gifts_for_user(self, repo, mock_datastore_client):
        mock_query = MagicMock()
        mock_datastore_client.query.return_value = mock_query

        data = {
            "sender_id": 1,
            "sender_name": "Sender",
            "receiver_id": 2,
            "gift_type": "palillo",
            "created_at": datetime.now(timezone.utc),
            "cost": 1,
        }
        entity = create_mock_entity(data)
        mock_query.fetch.return_value = [entity]

        gifts = await repo.get_gifts_for_user(2)

        assert len(gifts) == 1
        assert gifts[0].receiver_id == 2
        mock_datastore_client.query.assert_called_with(kind="Gift")
        mock_query.add_filter.assert_called_with("receiver_id", "=", 2)
