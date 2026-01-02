import pytest
from unittest.mock import MagicMock, patch
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient

from services.badge_service import BADGES
from models.user import User


@pytest.fixture
def mock_get_phrases():
    with patch("services.phrase_repo.get_phrases") as mock:
        yield mock


@pytest.fixture
def mock_get_long_phrases():
    with patch("services.long_phrase_repo.get_phrases") as mock:
        yield mock


@pytest.fixture
def mock_proposal_load_all():
    with patch("services.proposal_repo.load_all") as mock:
        yield mock


@pytest.fixture
def mock_long_proposal_load_all():
    with patch("services.long_proposal_repo.load_all") as mock:
        yield mock


@pytest.fixture
def mock_user_load_all():
    with patch("services.user_repo.load_all") as mock:
        yield mock


def test_metrics_endpoint_structure(
    client: TestClient,
    mock_user_load_all: MagicMock,
    mock_get_phrases: MagicMock,
    mock_get_long_phrases: MagicMock,
    mock_proposal_load_all: MagicMock,
    mock_long_proposal_load_all: MagicMock,
):
    """Test that the metrics endpoint loads and displays badge stats."""
    # Setup mock data
    mock_get_phrases.return_value = []
    mock_get_long_phrases.return_value = []
    mock_proposal_load_all.return_value = []
    mock_long_proposal_load_all.return_value = []

    # Mock users with badges
    user1 = MagicMock()
    user1.badges = ["madrugador", "visionario"]
    user2 = MagicMock()
    user2.badges = ["madrugador"]
    mock_user_load_all.return_value = [user1, user2]

    response = client.get("/metrics")

    assert response.status_code == HTTP_200_OK
    content = response.text

    # Check for new section title
    assert "Ecosistema de Medallas" in content

    # Check for badge name (ID is not shown)
    assert "El del primer café" in content

    # Check counts - user1 and user2 have madrugador -> count 2
    assert "2 usuarios" in content

    # Check visionario
    assert "Ojo de Halcón" in content


def test_ranking_endpoint_structure(
    client: TestClient,
    mock_user_load_all: MagicMock,
):
    """Test that the ranking endpoint includes the Insignias column."""
    user1 = User(id=123, name="Test User", points=100)
    user1.badges = ["madrugador"]

    mock_user_load_all.return_value = [user1]

    response = client.get("/ranking")

    assert response.status_code == HTTP_200_OK
    content = response.text

    # Check table headers
    assert "Insignias" in content
    assert "Puntos Totales" in content

    # Check if badge icon is rendered (madrugador icon is ☕)
    badge_icon = next(b.icon for b in BADGES if b.id == "madrugador")
    assert badge_icon in content
