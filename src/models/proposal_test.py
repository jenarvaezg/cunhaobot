import pytest
from unittest.mock import MagicMock, patch
from models.proposal import Proposal, LongProposal, get_proposal_class_by_kind


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
        p.save()
        self.mock_client.key.assert_called_with("Proposal", "123")
        self.mock_client.put.assert_called()

    def test_load_success(self):
        e = MagicMock()
        e.key.name = "ID"
        e.__getitem__.side_effect = lambda x: [] if "by" in x else "val"
        self.mock_client.get.return_value = e
        p = Proposal.load("ID")
        assert p.id == "ID"

    def test_load_all(self):
        self.mock_client.query.return_value.fetch.return_value = [
            {"from_chat_id": 1, "from_message_id": 2, "text": "T", "user_id": 3}
        ]
        # mock from_entity to avoid key.name access on dict
        with patch.object(Proposal, "from_entity") as mock_from:
            Proposal.load_all()
            mock_from.assert_called()

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
        # From missing_lines_test.py
        e = MagicMock()
        e.key.name = "ID"
        e.__getitem__.side_effect = lambda x: [] if "by" in x else "val"
        p = Proposal.from_entity(e)
        assert p.id == "ID"

    def test_proposal_load_early_return(self):
        # From missing_lines_test.py
        self.mock_client.get.return_value = None
        assert Proposal.load("999") is None

    @patch("models.proposal.Proposal.load_all")
    def test_get_proposals(self, mock_load_all):
        p1 = Proposal("1", 100, 200, "foo", user_id=1)
        p2 = Proposal("2", 101, 201, "bar", user_id=0)
        mock_load_all.return_value = [p1, p2]

        assert Proposal.get_proposals("fo") == [p1]
        assert Proposal.get_proposals(user_id=1) == [p1]
        assert Proposal.get_proposals(user_id=0) == [p1, p2]  # skips because 0 is falsy
        assert Proposal.get_proposals(id="__EMPTY__") == []


def test_get_proposal_class_by_kind():
    assert get_proposal_class_by_kind("Proposal") == Proposal
    assert get_proposal_class_by_kind("LongProposal") == LongProposal
