from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from models.proposal import Proposal, LongProposal
from infrastructure.datastore.proposal import ProposalDatastoreRepository


def create_mock_entity(data, kind="Proposal", entity_id="test_id"):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get

    def setitem(key, value):
        data[key] = value

    m.__setitem__.side_effect = setitem
    m.update.side_effect = data.update
    m.key.name = entity_id
    m.key.kind = kind
    m.key.id = entity_id
    return m


class TestProposalRepository:
    @pytest.fixture
    def repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        return ProposalDatastoreRepository(Proposal)

    @pytest.fixture
    def long_repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        return ProposalDatastoreRepository(LongProposal)

    def test_entity_to_domain_with_defaults(self, repo):
        # Test default values for missing fields
        data = {
            "from_chat_id": 1,
            "from_message_id": 2,
            "text": "default proposal",
            "liked_by": [],
            "disliked_by": [],
            "user_id": 0,
            "voting_ended": False,
        }
        entity = create_mock_entity(data, entity_id="default_id")

        proposal = repo._entity_to_domain(entity)
        assert proposal.id == "default_id"
        assert proposal.text == "default proposal"
        assert proposal.liked_by == []
        assert proposal.disliked_by == []
        assert proposal.user_id == 0
        assert proposal.voting_ended is False
        assert proposal.voting_ended_at is None
        assert proposal.created_at is None

    @pytest.mark.asyncio
    async def test_load(self, repo, mock_datastore_client):
        data = {"from_chat_id": 1, "from_message_id": 2, "text": "val"}
        entity = create_mock_entity(data, entity_id="ID1")
        mock_datastore_client.get.return_value = entity

        p = await repo.load("ID1")
        assert p.id == "ID1"
        mock_datastore_client.get.assert_called_once_with(repo.get_key("ID1"))
        mock_datastore_client.reset_mock()  # Reset mock calls

        # Test load not found
        mock_datastore_client.get.return_value = None
        p = await repo.load("non_existent")
        assert p is None

    @pytest.mark.asyncio
    async def test_load_all(self, repo, mock_datastore_client):
        mock_query = MagicMock()
        mock_datastore_client.query.return_value = mock_query

        entity1 = create_mock_entity(
            {"from_chat_id": 1, "from_message_id": 1, "text": "prop1"}, entity_id="1"
        )
        mock_query.fetch.return_value = [entity1]

        proposals = await repo.load_all()
        assert len(proposals) == 1
        assert proposals[0].id == "1"
        mock_datastore_client.query.assert_called_with(kind="Proposal")

    @pytest.mark.asyncio
    async def test_get_proposals_filter(self, repo, mock_datastore_client):
        p1 = Proposal(id="1", user_id=100)
        p2 = Proposal(id="2", user_id=0)

        # Use patch to mock load_all which is async
        with patch.object(repo, "load_all", new_callable=AsyncMock) as mock_load_all:
            mock_load_all.return_value = [p1, p2]

            # Test __EMPTY__ filter (user_id=0 is considered empty if we check truthiness,
            # but the code uses not getattr(p, field, None))
            res = await repo.get_proposals(user_id="__EMPTY__")
            assert len(res) == 1
            assert res[0].id == "2"

    @pytest.mark.asyncio
    async def test_save(self, repo, mock_datastore_client):
        p = Proposal(id="123", from_chat_id=456, from_message_id=789, text="test")
        await repo.save(p)
        mock_datastore_client.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_proposals_search_filter_limit_offset(
        self, repo, mock_datastore_client
    ):
        p1 = Proposal(
            id="1",
            from_chat_id=1,
            from_message_id=1,
            text="cuñao text",
            voting_ended=False,
        )
        p2 = Proposal(
            id="2",
            from_chat_id=2,
            from_message_id=2,
            text="other text",
            voting_ended=True,
        )
        p3 = Proposal(
            id="3",
            from_chat_id=1,
            from_message_id=3,
            text="another cuñao",
            voting_ended=False,
        )

        mock_query = MagicMock()
        mock_datastore_client.query.return_value = mock_query
        mock_query.fetch.return_value = [
            create_mock_entity(p1.model_dump(), entity_id="1"),
            create_mock_entity(p2.model_dump(), entity_id="2"),
            create_mock_entity(p3.model_dump(), entity_id="3"),
        ]

        # Test search
        results = await repo.get_proposals(search="cuñao")
        assert len(results) == 2
        assert {p.id for p in results} == {"1", "3"}

        # Test filter by field and value
        repo.clear_cache()
        mock_datastore_client.query.reset_mock()
        mock_query = MagicMock()
        mock_datastore_client.query.return_value = mock_query
        mock_query.fetch.return_value = [
            create_mock_entity(p1.model_dump(), entity_id="1"),
            create_mock_entity(p3.model_dump(), entity_id="3"),
        ]
        results = await repo.get_proposals(from_chat_id=1)
        assert len(results) == 2
        assert {p.id for p in results} == {"1", "3"}
        assert {p.id for p in results} == {"1", "3"}

        # Test filter by empty field
        p1.liked_by = ["1"]  # Add a liked_by to p1
        mock_query.fetch.return_value = [
            create_mock_entity(p1.model_dump(), entity_id="1"),
            create_mock_entity(p2.model_dump(), entity_id="2"),
        ]
        repo.clear_cache()
        results = await repo.get_proposals(liked_by="__EMPTY__")
        assert len(results) == 1
        assert results[0].id == "2"  # p2 has empty liked_by

        # Test limit and offset
        entities = [
            create_mock_entity(p1.model_dump(), entity_id="1"),
            create_mock_entity(p2.model_dump(), entity_id="2"),
            create_mock_entity(p3.model_dump(), entity_id="3"),
        ]

        def mock_fetch(limit=None, offset=0):
            res = entities[offset:]
            if limit:
                res = res[:limit]
            return res

        mock_query.fetch.side_effect = mock_fetch
        repo.clear_cache()
        results = await repo.get_proposals(limit=2, offset=1)
        assert len(results) == 2
        assert results[0].id == "2"
        assert results[1].id == "3"
