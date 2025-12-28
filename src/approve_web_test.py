import pytest
from litestar.status_codes import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from litestar.testing import TestClient
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
from main import app
from models.proposal import Proposal


@pytest.fixture
def client():
    with TestClient(app=app) as client:
        yield client


def test_approve_proposal_web_unauthorized(client):
    with patch(
        "litestar.connection.Request.session", new_callable=PropertyMock
    ) as mock_session:
        mock_session.return_value = {}

        with patch.dict("os.environ", {"GAE_ENV": "standard"}):
            rv = client.post("/proposals/Proposal/123/approve")

            assert rv.status_code == HTTP_401_UNAUTHORIZED


@patch("main.OWNER_ID", "12345")
@patch("main.get_tg_application")
@patch("main.approve_proposal", new_callable=AsyncMock)
def test_approve_proposal_web_auto_login_success(mock_approve, mock_get_app, client):
    # We don't set the session here, auto_login_local should do it

    # We need to make sure GAE_ENV is NOT 'standard'

    with patch.dict("os.environ", {"GAE_ENV": "local", "OWNER_ID": "12345"}):
        mock_proposal = MagicMock(spec=Proposal)

        mock_proposal.kind = "Proposal"

        mock_proposal.id = "123"

        with patch("main.get_proposal_class_by_kind") as mock_get_class:
            mock_class = MagicMock()

            mock_class.load.return_value = mock_proposal

            mock_get_class.return_value = mock_class

            mock_app = MagicMock()

            mock_app.initialize = AsyncMock()

            mock_app.bot = MagicMock()

            mock_get_app.return_value = mock_app

            rv = client.post("/proposals/Proposal/123/approve")

            assert rv.status_code == HTTP_200_OK

            assert rv.text == "Approved"


@patch("main.OWNER_ID", "12345")
def test_approve_proposal_web_not_found(client):
    with patch(
        "litestar.connection.Request.session", new_callable=PropertyMock
    ) as mock_session:
        mock_session.return_value = {"user": {"id": "12345"}}

        with patch("main.get_proposal_class_by_kind") as mock_get_class:
            mock_class = MagicMock()
            mock_class.load.return_value = None
            mock_get_class.return_value = mock_class

            rv = client.post("/proposals/Proposal/123/approve")
            assert rv.status_code == HTTP_404_NOT_FOUND


@patch("main.OWNER_ID", "12345")
@patch("main.get_tg_application")
@patch("main.approve_proposal", new_callable=AsyncMock)
def test_approve_proposal_web_success(mock_approve, mock_get_app, client):
    with patch(
        "litestar.connection.Request.session", new_callable=PropertyMock
    ) as mock_session:
        mock_session.return_value = {"user": {"id": "12345"}}

        mock_proposal = MagicMock(spec=Proposal)
        mock_proposal.kind = "Proposal"
        mock_proposal.id = "123"

        with patch("main.get_proposal_class_by_kind") as mock_get_class:
            mock_class = MagicMock()
            mock_class.load.return_value = mock_proposal
            mock_get_class.return_value = mock_class

            mock_app = MagicMock()
            mock_app.initialize = AsyncMock()
            mock_app.bot = MagicMock()
            mock_get_app.return_value = mock_app

            rv = client.post("/proposals/Proposal/123/approve")
            assert rv.status_code == HTTP_200_OK
            assert rv.text == "Approved"

            mock_app.initialize.assert_called_once()
            mock_approve.assert_called_once_with(mock_proposal, mock_app.bot)
