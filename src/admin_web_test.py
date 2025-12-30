from unittest.mock import patch, AsyncMock


def test_approve_proposal_success(client):
    with (
        patch(
            "services.proposal_service.ProposalService.approve",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch("core.config.config.is_gae", False),
    ):
        rv = client.post("/admin/proposals/Proposal/123/approve")
        assert rv.status_code == 200


def test_approve_proposal_not_found(client):
    # Correct path is /admin/proposals/...
    with (
        patch(
            "services.proposal_service.ProposalService.approve",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch("core.config.config.is_gae", False),
    ):
        rv = client.post("/admin/proposals/Proposal/nonexistent/approve")
        assert rv.status_code == 404


def test_reject_proposal_success(client):
    with (
        patch(
            "services.proposal_service.ProposalService.reject",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch("core.config.config.is_gae", False),
    ):
        rv = client.post("/admin/proposals/Proposal/123/reject")
        assert rv.status_code == 200


def test_reject_proposal_not_found(client):
    with (
        patch(
            "services.proposal_service.ProposalService.reject",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch("core.config.config.is_gae", False),
    ):
        rv = client.post("/admin/proposals/Proposal/123/reject")
        assert rv.status_code == 404
