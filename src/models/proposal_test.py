from models.proposal import Proposal, LongProposal, get_proposal_class_by_kind


class TestProposal:
    def test_proposal_init(self):
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


class TestLongProposal:
    def test_long_proposal_init(self):
        lp = LongProposal(
            id="123",
            from_chat_id=456,
            from_message_id=789,
            text="test",
        )
        assert lp.kind == "LongProposal"


class TestProposalFunctions:
    def test_get_proposal_class_by_kind_long_proposal(self):
        cls = get_proposal_class_by_kind("LongProposal")
        assert cls == LongProposal

    def test_get_proposal_class_by_kind_proposal(self):
        cls = get_proposal_class_by_kind("Proposal")
        assert cls == Proposal

    def test_get_proposal_class_by_kind_unknown(self):
        cls = get_proposal_class_by_kind("UnknownKind")
        assert cls == Proposal
