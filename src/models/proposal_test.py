import pytest
from unittest.mock import MagicMock, patch
from models.proposal import (
    Proposal,
    LongProposal,
    get_proposal_class_by_kind,
    DatastoreProposalRepository,
)


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


class TestProposal:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        self.mock_client = mock_datastore_client
        self.mock_client.reset_mock()

    def test_init(self):
        p = Proposal(
            id="123",
            from_chat_id=456,
            from_message_id=789,
            text="test proposal",
            user_id=111,
        )
        assert p.id == "123"
        assert p.text == "test proposal"
        assert p.liked_by == []
        assert p.disliked_by == []

    def test_add_vote_positive(self):
        p = Proposal(id="123", from_chat_id=456, from_message_id=789, text="test")
        p.add_vote(positive=True, voter_id=1)
        assert p.liked_by == [1]
        assert p.disliked_by == []

    def test_add_vote_negative(self):
        p = Proposal(id="123", from_chat_id=456, from_message_id=789, text="test")
        p.add_vote(positive=False, voter_id=2)
        assert p.disliked_by == [2]
        assert p.liked_by == []

    def test_add_vote_switch(self):
        p = Proposal(
            id="123", from_chat_id=456, from_message_id=789, text="test", liked_by=[1]
        )
        p.add_vote(positive=False, voter_id=1)
        assert p.liked_by == []
        assert p.disliked_by == [1]

    def test_from_update(self):
        update = MagicMock()
        update.effective_message.chat.id = 100
        update.effective_message.message_id = 50
        update.effective_message.text = "/proponer some text"
        update.effective_user.id = 200

        p = Proposal.from_update(update)
        assert p.id == "150"
        assert p.from_chat_id == 100
        assert p.text == "some text"
        assert p.user_id == 200

    def test_from_update_with_text(self):
        update = MagicMock()
        update.effective_message.chat.id = 100
        update.effective_message.message_id = 50
        update.effective_message.text = "ignored text"
        update.effective_user.id = 200

        p = Proposal.from_update(update, text="explicit text")
        assert p.text == "explicit text"

    def test_proposal_text_from_message_no_command(self):
        message = MagicMock()
        message.text = "Just a plain message"
        assert Proposal.proposal_text_from_message(message) == "Just a plain message"

    def test_proposal_text_from_message_reply(self):
        message = MagicMock()
        message.text = "/proponer"
        message.reply_to_message.text = "replied text"

        text = Proposal.proposal_text_from_message(message)
        assert text == "replied text"

    def test_proposal_text_from_message_no_text(self):
        message = MagicMock()
        message.text = None
        assert Proposal.proposal_text_from_message(message) == ""

    def test_save(self):
        p = Proposal(id="123", from_chat_id=456, from_message_id=789, text="test")

        # We need to verify that datastore put is called
        # The new save calls get_repository().save(self)
        # get_repository() uses get_datastore_client() which is mocked via conftest?
        # Yes, conftest mocks google.cloud.datastore

        # But get_datastore_client in utils.gcp creates a NEW client instance each call.
        # conftest mocks the class constructor.
        # So self.mock_client is the return value of constructor.

        p.save()
        self.mock_client.key.assert_called_with("Proposal", "123")
        self.mock_client.put.assert_called()

    def test_load_success(self):
        data = {
            "from_chat_id": 1,
            "from_message_id": 2,
            "text": "val",
            "liked_by": [],
            "disliked_by": [],
            "user_id": 0,
        }
        e = create_mock_entity(data, key_name="ID")
        self.mock_client.get.return_value = e

        p = Proposal.load("ID")
        assert p.id == "ID"
        assert p.text == "val"

    def test_load_all(self):
        data = {"from_chat_id": 1, "from_message_id": 2, "text": "T", "user_id": 3}
        e = create_mock_entity(data, key_name="ID")
        self.mock_client.query.return_value.fetch.return_value = [e]

        proposals = Proposal.load_all()
        assert len(proposals) == 1
        assert proposals[0].text == "T"

    def test_delete(self):
        p = Proposal(id="123", from_chat_id=4, from_message_id=5, text="T")
        p.delete()
        self.mock_client.delete.assert_called()

    def test_from_update_no_msg(self):
        update = MagicMock()
        update.effective_message = None
        with pytest.raises(ValueError):
            Proposal.from_update(update)

    def test_proposal_no_text_extra(self):
        # From missing_lines_test.py
        m = MagicMock()
        m.text = None
        assert Proposal.proposal_text_from_message(m) == ""

    def test_proposal_from_entity_id(self):
        # Test repo internal method
        data = {"from_chat_id": 1, "from_message_id": 2, "text": "T", "user_id": 3}
        e = create_mock_entity(data, key_name="ID")

        repo = Proposal.get_repository()
        if isinstance(repo, DatastoreProposalRepository):
            p = repo._entity_to_domain(e)
            assert p.id == "ID"

    def test_proposal_load_early_return(self):
        # From missing_lines_test.py
        self.mock_client.get.return_value = None
        assert Proposal.load("999") is None

    def test_get_proposals(self):
        p1 = Proposal("1", 100, 200, "foo", user_id=1)
        p2 = Proposal("2", 101, 201, "bar", user_id=0)

        # Patch load_all on the repository instance or on the Facade
        with patch.object(Proposal.get_repository(), "load_all", return_value=[p1, p2]):
            assert Proposal.get_proposals("fo") == [p1]
            assert Proposal.get_proposals(user_id=1) == [p1]
            assert Proposal.get_proposals(user_id=0) == [
                p1,
                p2,
            ]  # skips because 0 is falsy
            assert Proposal.get_proposals(id="__EMPTY__") == []


def test_get_proposal_class_by_kind():
    assert get_proposal_class_by_kind("Proposal") == Proposal
    assert get_proposal_class_by_kind("LongProposal") == LongProposal
