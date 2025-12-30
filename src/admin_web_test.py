import pytest
from litestar.status_codes import HTTP_200_OK
from unittest.mock import patch, AsyncMock, MagicMock
from core.config import config


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {config.session_secret}"}


def test_orphans_unauthorized(client):
    with patch("core.config.config.is_gae", True):
        rv = client.get("/admin/orphans")
        assert rv.status_code == 401


def test_orphans_authorized(client):
    with (
        patch(
            "services.proposal_service.ProposalService.get_curators",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch("services.phrase_repo.load_all", return_value=[]),
        patch("services.long_phrase_repo.load_all", return_value=[]),
        patch("core.config.config.is_gae", False),  # auto login
    ):
        rv = client.get("/admin/orphans")
        assert rv.status_code == HTTP_200_OK


def test_link_orphan_not_found(client):
    with (
        patch("services.phrase_repo.load", return_value=None),
        patch("core.config.config.is_gae", False),
    ):
        rv = client.post(
            "/admin/orphans/link", json={"phrase_text": "none", "kind": "Phrase"}
        )
        assert rv.status_code == 404


def test_manual_link_not_found(client):
    with (
        patch("services.phrase_repo.load", return_value=None),
        patch("core.config.config.is_gae", False),
    ):
        rv = client.post(
            "/admin/orphans/manual-link", json={"phrase_text": "none", "kind": "Phrase"}
        )
        assert rv.status_code == 404


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


def test_link_orphan_success(client):
    mock_phrase = MagicMock()
    with (
        patch("services.phrase_repo.load", return_value=mock_phrase),
        patch("services.phrase_repo.save") as mock_save,
        patch("core.config.config.is_gae", False),
    ):
        rv = client.post(
            "/admin/orphans/link",
            json={"phrase_text": "foo", "kind": "Phrase", "proposal_id": "1"},
        )
        assert rv.status_code == 200
        assert mock_phrase.proposal_id == "1"
        mock_save.assert_called_once()


def test_manual_link_success(client):
    mock_phrase = MagicMock()
    with (
        patch("services.phrase_repo.load", return_value=mock_phrase),
        patch("services.phrase_repo.save") as mock_save,
        patch("core.config.config.is_gae", False),
    ):
        rv = client.post(
            "/admin/orphans/manual-link",
            json={
                "phrase_text": "foo",
                "kind": "Phrase",
                "creator_id": "1",
                "chat_id": "2",
                "date": "2025-12-30T10:00:00",
            },
        )
        assert rv.status_code == 200
        mock_save.assert_called_once()
