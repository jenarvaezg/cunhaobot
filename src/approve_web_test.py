from litestar.status_codes import HTTP_200_OK, HTTP_401_UNAUTHORIZED
from unittest.mock import patch, AsyncMock, PropertyMock


def test_approve_proposal_web_unauthorized(client):
    with patch(
        "litestar.connection.Request.session", new_callable=PropertyMock
    ) as mock_session:
        mock_session.return_value = {}

        with patch("core.config.config.is_gae", True):
            rv = client.post("/admin/proposals/Proposal/123/approve")
            assert rv.status_code == HTTP_401_UNAUTHORIZED


def test_approve_proposal_web_auto_login_success(client):
    with (
        patch.dict("os.environ", {"GAE_ENV": "local", "OWNER_ID": "12345"}),
        patch("core.config.config.owner_id", "12345"),
        patch("core.config.config.is_gae", False),
        patch(
            "services.proposal_service.ProposalService.approve", new_callable=AsyncMock
        ) as mock_approve,
    ):
        mock_approve.return_value = True

        rv = client.post("/admin/proposals/Proposal/123/approve")

        assert rv.status_code == HTTP_200_OK
        assert rv.text == "Approved"


def test_approve_proposal_web_success(client):
    with (
        patch(
            "litestar.connection.Request.session", new_callable=PropertyMock
        ) as mock_session,
        patch("core.config.config.owner_id", "12345"),
        patch(
            "services.proposal_service.ProposalService.approve", new_callable=AsyncMock
        ) as mock_approve,
    ):
        mock_session.return_value = {"user": {"id": "12345"}}
        mock_approve.return_value = True

        rv = client.post("/admin/proposals/Proposal/123/approve")
        assert rv.status_code == HTTP_200_OK
        assert rv.text == "Approved"


def test_reject_proposal_web_success(client):
    with (
        patch(
            "litestar.connection.Request.session", new_callable=PropertyMock
        ) as mock_session,
        patch("core.config.config.owner_id", "12345"),
        patch(
            "services.proposal_service.ProposalService.reject", new_callable=AsyncMock
        ) as mock_reject,
    ):
        mock_session.return_value = {"user": {"id": "12345"}}
        mock_reject.return_value = True

        rv = client.post("/admin/proposals/Proposal/123/reject")
        assert rv.status_code == HTTP_200_OK
        assert rv.text == "Rejected"
