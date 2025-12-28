import pytest
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient
from unittest.mock import patch
from main import app
from models.phrase import Phrase, LongPhrase


@pytest.fixture
def client():
    with TestClient(app=app) as client:
        yield client


def test_index_page(client):
    p1 = Phrase(text="p1", usages=10)
    lp1 = LongPhrase(text="lp1", usages=5)

    with (
        patch("models.phrase.Phrase.get_phrases", return_value=[p1]),
        patch("models.phrase.LongPhrase.get_phrases", return_value=[lp1]),
    ):
        rv = client.get("/")
        assert rv.status_code == HTTP_200_OK
        assert "El Archivo del Cuñao" in rv.text
        assert "p1" in rv.text
        assert "Lp1" in rv.text
        assert "Total: 10" in rv.text
        assert "Total: 5" in rv.text


def test_search_endpoint(client):
    p1 = Phrase(text="match", usages=10)

    with (
        patch("models.phrase.Phrase.get_phrases", return_value=[p1]),
        patch("models.phrase.LongPhrase.get_phrases", return_value=[]),
    ):
        rv = client.get("/search", params={"search": "match"})
        assert rv.status_code == HTTP_200_OK
        assert "match" in rv.text
        # Check that it returns the partial, not the full layout
        assert "El Archivo del Cuñao" not in rv.text
        assert "Palabras Poderosas" in rv.text
