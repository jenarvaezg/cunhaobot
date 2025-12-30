from unittest.mock import patch


def test_metrics_page(client):
    from models.proposal import Proposal

    p0 = Proposal(id="0", user_id=0, voting_ended=False)
    with (
        patch("services.proposal_repo.load_all", return_value=[p0]),
        patch("services.long_proposal_repo.load_all", return_value=[]),
        patch("services.phrase_repo.get_phrases", return_value=[]),
        patch("services.long_phrase_repo.get_phrases", return_value=[]),
    ):
        rv = client.get("/metrics")
        assert rv.status_code == 200
