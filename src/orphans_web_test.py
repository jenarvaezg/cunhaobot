import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from models.phrase import Phrase


@pytest.fixture
def auth_user():
    return {"id": "123", "first_name": "Test", "username": "testuser"}


@pytest.fixture
def owner_id():
    return "123"


def test_orphans_page_unauthorized(client):
    # Forzamos sesión vacía
    with patch(
        "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
    ) as mock_session:
        mock_session.return_value = {}
        rv = client.get("/orphans")
        assert rv.status_code == 401


def test_orphans_page_authorized(client, auth_user, owner_id):
    p1 = Phrase(text="Orphan", proposal_id="")
    # Forzamos que config.owner_id coincida con auth_user['id']
    with (
        patch("main.Phrase.get_phrases", return_value=[p1]),
        patch("main.LongPhrase.get_phrases", return_value=[]),
        patch("main.Proposal.load_all", return_value=[]),
        patch("main.LongProposal.load_all", return_value=[]),
        patch("main.User.load_all", return_value=[]),
        patch("main.InlineUser.get_all", return_value=[]),
        patch("main.config.owner_id", owner_id),
        patch(
            "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
        ) as mock_session,
    ):
        mock_session.return_value = {"user": auth_user}
        rv = client.get("/orphans")
        assert rv.status_code == HTTP_200_OK
        assert "CASAMIENTO DE FRASES" in rv.text
        assert "Orphan" in rv.text


def test_link_orphan_web_success(client, auth_user, owner_id):
    p1 = Phrase(text="Orphan", proposal_id="")
    mock_repo = MagicMock()

    with (
        patch("main.Phrase.get_repository", return_value=mock_repo),
        patch("main.config.owner_id", owner_id),
        patch(
            "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
        ) as mock_session,
    ):
        mock_repo.get_phrases.return_value = [p1]
        mock_session.return_value = {"user": auth_user}

        payload = {"phrase_text": "Orphan", "kind": "Phrase", "proposal_id": "prop123"}

        rv = client.post("/orphans/link", json=payload)
        assert rv.status_code == HTTP_200_OK
        assert rv.text == "Linked"
        assert p1.proposal_id == "prop123"
        mock_repo.save.assert_called_once_with(p1)


def test_link_orphan_web_phrase_not_found(client, auth_user, owner_id):
    mock_repo = MagicMock()
    with (
        patch("main.Phrase.get_repository", return_value=mock_repo),
        patch("main.config.owner_id", owner_id),
        patch(
            "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
        ) as mock_session,
    ):
        mock_repo.get_phrases.return_value = []
        mock_session.return_value = {"user": auth_user}

        payload = {"phrase_text": "Unknown", "kind": "Phrase", "proposal_id": "prop123"}

        rv = client.post("/orphans/link", json=payload)
        assert rv.status_code == HTTP_404_NOT_FOUND
