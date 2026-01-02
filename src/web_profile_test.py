from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from unittest.mock import patch, AsyncMock
from models.user import User
from models.phrase import Phrase


def test_profile_page_success(client):
    user = User(id="123", name="Test User", points=150, platform="telegram")
    p1 = Phrase(text="p1", usages=10, user_id="123")

    with (
        patch("services.user_repo.load", return_value=user),
        patch(
            "services.usage_service.UsageService.get_user_stats",
            return_value={"total_usages": 50},
        ),
        patch(
            "services.badge_service.BadgeService.get_all_badges_progress",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("services.phrase_repo.get_phrases", return_value=[p1]),
        patch("services.long_phrase_repo.get_phrases", return_value=[]),
    ):
        rv = client.get("/user/123/profile")
        assert rv.status_code == HTTP_200_OK
        assert "Test User" in rv.text
        assert "150 pts" in rv.text
        assert "50 usos" in rv.text
        assert "Lvl. 2" in rv.text  # 1 + 150/100 = 2


def test_profile_page_not_found(client):
    with patch("services.user_repo.load", return_value=None):
        rv = client.get("/user/999/profile")
        assert rv.status_code == HTTP_404_NOT_FOUND
