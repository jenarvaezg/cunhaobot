import pytest
from unittest.mock import patch, PropertyMock, AsyncMock
from litestar.status_codes import HTTP_200_OK
from models.phrase import Phrase


@pytest.fixture
def auth_user():
    return {"id": "123", "username": "testuser", "first_name": "Test"}


@pytest.fixture
def owner_id():
    return "123"


def test_orphans_page_unauthorized(client):
    # Forzamos sesión vacía
    with (
        patch(
            "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
        ) as mock_session,
        patch("core.config.config.is_gae", True),
    ):
        mock_session.return_value = {}
        rv = client.get("/admin/orphans")
        assert rv.status_code == 401


def test_orphans_page_authorized(client, auth_user, owner_id):
    p1 = Phrase(text="Orphan", proposal_id="")

    # Forzamos que config.owner_id coincida con auth_user['id']
    with (
        patch("services.phrase_repo.load_all", return_value=[p1]),
        patch("services.long_phrase_repo.load_all", return_value=[]),
        patch(
            "services.proposal_service.ProposalService.get_curators",
            new_callable=AsyncMock,
            return_value={1: "user1"},
        ),
        patch("core.config.config.owner_id", owner_id),
        patch("core.config.config.is_gae", False),
        patch(
            "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
        ) as mock_session,
    ):
        mock_session.return_value = {"user": auth_user}
        rv = client.get("/admin/orphans")
        assert rv.status_code == HTTP_200_OK
        assert "CASAMIENTO DE FRASES" in rv.text


def test_link_orphan_web_success(client, auth_user, owner_id):
    p1 = Phrase(text="Orphan", proposal_id="")

    with (
        patch("services.phrase_repo.load", return_value=p1),
        patch("services.phrase_repo.save") as mock_save,
        patch("core.config.config.owner_id", owner_id),
        patch("core.config.config.is_gae", False),
        patch(
            "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
        ) as mock_session,
    ):
        mock_session.return_value = {"user": auth_user}

        payload = {"phrase_text": "Orphan", "kind": "Phrase", "proposal_id": "prop123"}

        rv = client.post("/admin/orphans/link", json=payload)
        assert rv.status_code == HTTP_200_OK
        assert rv.text == "Linked"
        assert p1.proposal_id == "prop123"
        mock_save.assert_called_once()


def test_manual_link_orphan_web_success(client, auth_user, owner_id):
    p1 = Phrase(text="ManualOrphan", proposal_id="")

    with (
        patch("services.phrase_repo.load", return_value=p1),
        patch("services.phrase_repo.save") as mock_save,
        patch("core.config.config.owner_id", owner_id),
        patch("core.config.config.is_gae", False),
        patch(
            "litestar.connection.base.ASGIConnection.session",
            new_callable=PropertyMock,
        ) as mock_session,
    ):
        mock_session.return_value = {"user": auth_user}

        payload = {
            "phrase_text": "ManualOrphan",
            "kind": "Phrase",
            "creator_id": 999,
            "date": "2025-01-01",
            "chat_id": 123,
        }

        rv = client.post("/admin/orphans/manual-link", json=payload)
        assert rv.status_code == HTTP_200_OK
        assert rv.text == "Linked"
        assert p1.user_id == 999
        assert p1.chat_id == 123
        mock_save.assert_called_once()
