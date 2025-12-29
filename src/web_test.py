from litestar.status_codes import HTTP_200_OK
from unittest.mock import patch
from models.phrase import Phrase, LongPhrase


def test_index_page(client):
    p1 = Phrase(text="p1", usages=10)
    lp1 = LongPhrase(text="esto es una prueba", usages=5)

    with (
        patch("main.Phrase.get_phrases", return_value=[p1]),
        patch("main.LongPhrase.get_phrases", return_value=[lp1]),
    ):
        rv = client.get("/")
        assert rv.status_code == HTTP_200_OK
        assert "EL ARCHIVO DEL CUÑAO" in rv.text
        assert "p1" in rv.text
        assert "Esto es una prueba." in rv.text
        # In the new design, usages are in a stat-badge
        assert '<span class="fw-bold">10</span>' in rv.text
        assert '<span class="fw-bold">5</span>' in rv.text


def test_search_endpoint(client):
    p1 = Phrase(text="match", usages=10)

    with (
        patch("main.Phrase.get_phrases", return_value=[p1]),
        patch("main.LongPhrase.get_phrases", return_value=[]),
    ):
        rv = client.get("/search", params={"search": "match"})
        assert rv.status_code == HTTP_200_OK
        assert "match" in rv.text
        # Check that it returns the partial, not the full layout
        assert "El Archivo del Cuñao" not in rv.text
        assert "Palabras Poderosas" in rv.text


def test_ping(client):
    rv = client.get("/ping")
    assert rv.status_code == HTTP_200_OK
    assert rv.text == "I am alive"


def test_auth_telegram_fail(client):
    rv = client.get("/auth/telegram", params={"hash": "wrong"})
    assert rv.status_code == HTTP_200_OK  # Redirects to /
    assert rv.url.path == "/"


def test_logout(client):
    rv = client.get("/logout")
    assert rv.status_code == HTTP_200_OK
    assert rv.url.path == "/"


def test_proposals(client):
    with (
        patch("main.Proposal.get_proposals", return_value=[]),
        patch("main.LongProposal.get_proposals", return_value=[]),
        patch("main.Phrase.get_phrases", return_value=[]),
        patch("main.LongPhrase.get_phrases", return_value=[]),
    ):
        rv = client.get("/proposals")
        assert rv.status_code == HTTP_200_OK
        assert "PROPUESTAS EN EL HORNO" in rv.text


def test_proposals_search(client):
    with (
        patch("main.Proposal.get_proposals", return_value=[]),
        patch("main.LongProposal.get_proposals", return_value=[]),
        patch("main.Phrase.get_phrases", return_value=[]),
        patch("main.LongPhrase.get_phrases", return_value=[]),
    ):
        rv = client.get("/proposals/search", headers={"HX-Request": "true"})
        assert rv.status_code == HTTP_200_OK
        assert "Apelativos en Espera" in rv.text


@patch("main.handle_slack")
@patch("requests.post")
def test_slack_handler(mock_post, mock_handle_slack, client):
    mock_handle_slack.return_value = {
        "direct": "direct_msg",
        "indirect": {"text": "indirect_msg"},
    }
    rv = client.post(
        "/slack", data={"payload": '{"response_url": "http://example.com"}'}
    )
    assert rv.status_code == HTTP_200_OK
    assert rv.text == "direct_msg"


def test_slack_auth(client):
    with patch.dict("os.environ", {"SLACK_CLIENT_ID": "test_id"}):
        rv = client.get("/slack/auth", follow_redirects=False)
        assert rv.status_code == 302
        assert "slack.com/oauth/v2/authorize" in rv.headers["location"]


@patch("requests.post")
def test_slack_auth_redirect(mock_post, client):
    with patch.dict(
        "os.environ",
        {"SLACK_CLIENT_ID": "test_id", "SLACK_CLIENT_SECRET": "test_secret"},
    ):
        rv = client.get("/slack/auth/redirect", params={"code": "test_code"})
        assert rv.status_code == HTTP_200_OK
        assert rv.text == ":)"
        mock_post.assert_called_once()
