from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from unittest.mock import patch, AsyncMock, PropertyMock
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from models.user import User


def test_index_page(client):
    p1 = Phrase(text="p1", usages=10)
    lp1 = LongPhrase(text="esto es una prueba", usages=5)

    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.load_all",
            new_callable=AsyncMock,
            return_value=[p1],
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.load_all",
            new_callable=AsyncMock,
            return_value=[lp1],
        ),
    ):
        rv = client.get("/")
        assert rv.status_code == HTTP_200_OK
        assert "EL ARCHIVO DEL CUÑAO" in rv.text
        assert "p1" in rv.text
        assert "esto es una prueba" in rv.text
        assert '<span class="fw-bold">10</span>' in rv.text
        assert '<span class="fw-bold">5</span>' in rv.text


def test_search_endpoint(client):
    p1 = Phrase(text="match", usages=10)

    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[p1],
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        rv = client.get("/search", params={"search": "match"})
        assert rv.status_code == HTTP_200_OK
        assert "match" in rv.text
        assert "El Archivo del Cuñao" not in rv.text
        assert "Palabras Poderosas" in rv.text


def test_ping(client):
    rv = client.get("/ping")
    assert rv.status_code == HTTP_200_OK
    assert rv.text == "I am alive"


def test_auth_telegram_fail(client):
    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        rv = client.get("/auth/telegram", params={"hash": "wrong"})
        assert rv.status_code == HTTP_200_OK  # After redirect to /
        assert rv.url.path == "/"


def test_logout(client):
    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        rv = client.get("/logout")
        assert rv.status_code == HTTP_200_OK  # After redirect to /
        assert rv.url.path == "/"


def test_proposals(client):
    with (
        patch(
            "infrastructure.datastore.proposal.proposal_repository.get_proposals",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "infrastructure.datastore.proposal.long_proposal_repository.get_proposals",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        rv = client.get("/proposals")
        assert rv.status_code == HTTP_200_OK
        assert "PROPUESTAS EN EL HORNO" in rv.text


def test_proposals_search(client):
    with (
        patch(
            "infrastructure.datastore.proposal.proposal_repository.get_proposals",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "infrastructure.datastore.proposal.long_proposal_repository.get_proposals",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        rv = client.get("/proposals/search", headers={"HX-Request": "true"})
        assert rv.status_code == HTTP_200_OK
        assert "Apelativos en Espera" in rv.text


def test_generate_ai_phrases_unauthorized(client):
    with patch("core.config.config.is_gae", True):
        rv = client.post("/ai/generate")
        assert rv.status_code == HTTP_401_UNAUTHORIZED
        assert rv.json() == {"error": "Unauthorized"}


def test_generate_ai_phrases_authorized_success(client):
    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.owner_id", "123"),
        patch(
            "services.ai_service.AIService.generate_cunhao_phrases",
            new_callable=AsyncMock,
            return_value=["phrase1", "phrase2"],
        ),
    ):
        # Simulate authorized user session
        with patch(
            "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
        ) as mock_session:
            mock_session.return_value = {"user": {"id": "123"}}
            rv = client.post("/ai/generate")
            assert rv.status_code == HTTP_200_OK
            assert rv.json() == {"phrases": ["phrase1", "phrase2"]}


def test_generate_ai_phrases_authorized_exception(client):
    with (
        patch("core.config.config.is_gae", False),
        patch("core.config.config.owner_id", "123"),
        patch(
            "services.ai_service.AIService.generate_cunhao_phrases",
            new_callable=AsyncMock,
            side_effect=Exception("AI Error"),
        ),
    ):
        # Simulate authorized user session
        with patch(
            "litestar.connection.base.ASGIConnection.session", new_callable=PropertyMock
        ) as mock_session:
            mock_session.return_value = {"user": {"id": "123"}}
            rv = client.post("/ai/generate")
            assert rv.status_code == HTTP_500_INTERNAL_SERVER_ERROR
            assert rv.json() == {"error": "AI Error"}


def test_metrics_page_empty_data(client):
    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "infrastructure.datastore.proposal.proposal_repository.load_all",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "infrastructure.datastore.proposal.long_proposal_repository.load_all",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "infrastructure.datastore.user.user_repository.load_all",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        rv = client.get("/metrics")
        assert rv.status_code == HTTP_200_OK
        # Check text content because context might not be directly accessible when template is rendered
        assert "0" in rv.text  # total_phrases and total_pending
        assert "Propuestas Aprobadas" in rv.text
        assert "Propuestas Pendientes" in rv.text


def test_metrics_page_with_data(client):
    p1 = Phrase(text="p1", usages=10, user_id=1)
    lp1 = LongPhrase(text="lp1", usages=5, user_id=2)

    prop1 = Proposal(id="1", user_id=1, voting_ended=False, text="prop1")
    lprop1 = LongProposal(id="2", user_id=3, voting_ended=False, text="lprop1")

    user1 = User(id=1, name="User One")
    user2 = User(id=2, name="User Two")
    user3 = User(id=3, name="User Three")

    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[p1],
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.get_phrases",
            new_callable=AsyncMock,
            return_value=[lp1],
        ),
        patch(
            "infrastructure.datastore.proposal.proposal_repository.load_all",
            new_callable=AsyncMock,
            return_value=[prop1],
        ),
        patch(
            "infrastructure.datastore.proposal.long_proposal_repository.load_all",
            new_callable=AsyncMock,
            return_value=[lprop1],
        ),
        patch(
            "infrastructure.datastore.user.user_repository.load_all",
            new_callable=AsyncMock,
            return_value=[user1, user2, user3],
        ),
    ):
        rv = client.get("/metrics")
        assert rv.status_code == HTTP_200_OK
        assert "2" in rv.text  # total_phrases
        assert "2" in rv.text  # total_pending
        assert "Ecosistema de Medallas" in rv.text


def test_phrase_detail_page(client):
    from datetime import datetime

    p1 = Phrase(
        id=123,
        text="p1",
        usages=10,
        user_id=12345,
        created_at=datetime.now(),
    )

    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.load",
            new_callable=AsyncMock,
            return_value=p1,
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.load",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "infrastructure.datastore.user.user_repository.load",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        rv = client.get("/phrase/123")
        assert rv.status_code == HTTP_200_OK
        assert "Detalle de Sabiduría" in rv.text
        assert "p1" in rv.text
        assert "12345" in rv.text
        assert "10" in rv.text


def test_phrase_detail_page_not_found(client):
    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.load",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.load",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        rv = client.get("/phrase/999")
        assert rv.status_code == 404


def test_phrase_sticker_route(client):
    p1 = Phrase(id=123, text="p1", sticker_file_id="file123")
    sticker_content = b"fake_png_content"

    with (
        patch(
            "infrastructure.datastore.phrase.phrase_repository.load",
            new_callable=AsyncMock,
            return_value=p1,
        ),
        patch(
            "infrastructure.datastore.phrase.long_phrase_repository.load",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "services.phrase_service.PhraseService.create_sticker_image",
            return_value=sticker_content,
        ),
    ):
        rv = client.get("/phrase/123/sticker.png")
        assert rv.status_code == 200
        assert rv.content == sticker_content
        assert rv.headers["content-type"] == "image/png"
        assert "max-age=31536000" in rv.headers["cache-control"]


def test_ranking_page(client):
    u1 = User(id=1, name="Cuñao Pro", points=100)
    u2 = User(id=2, name="Cuñao Junior", points=50)

    with (
        patch(
            "infrastructure.datastore.user.user_repository.load_all",
            new_callable=AsyncMock,
            return_value=[u1, u2],
        ),
    ):
        rv = client.get("/ranking")
        assert rv.status_code == HTTP_200_OK
        assert "RANKING DE CUÑADISMO" in rv.text
        assert "Cuñao Pro" in rv.text
        assert "100" in rv.text
        assert "Cuñao Junior" in rv.text
        assert "50" in rv.text


def test_ai_phrase_success(client):
    with patch(
        "services.ai_service.AIService.generate_cunhao_phrases",
        new_callable=AsyncMock,
        return_value=["AI phrase"],
    ):
        rv = client.get("/ai/phrase")
        assert rv.status_code == 200
        assert "AI phrase" in rv.text
        assert "PERLA DE IA" in rv.text


def test_privacy_page(client):
    rv = client.get("/privacy")
    assert rv.status_code == HTTP_200_OK
    assert "Política de Privacidad" in rv.text
    assert "GDPR" in rv.text


def test_terms_page(client):
    rv = client.get("/terms")
    assert rv.status_code == HTTP_200_OK
    assert "Términos de Servicio" in rv.text
    assert "Aceptación" in rv.text


def test_data_policy_page(client):
    rv = client.get("/data-policy")
    assert rv.status_code == HTTP_200_OK
    assert "Política de Datos" in rv.text
    assert "Retención" in rv.text
