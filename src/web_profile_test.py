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


def test_profile_page_slack_user(client):
    # Slack ID is alphanumeric
    user = User(id="U12345", name="Slack User", points=100, platform="slack")

    with (
        patch("services.user_repo.load", return_value=user),
        patch(
            "services.usage_service.UsageService.get_user_stats",
            return_value={"total_usages": 10},
        ),
        patch(
            "services.badge_service.BadgeService.get_all_badges_progress",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("services.phrase_repo.get_phrases", return_value=[]),
        patch("services.long_phrase_repo.get_phrases", return_value=[]),
        patch("services.poster_request_repo.get_completed_by_user", return_value=[]),
        patch(
            "infrastructure.datastore.gift.gift_repository.get_gifts_for_user",
            new_callable=AsyncMock,
        ) as mock_gifts,
    ):
        rv = client.get("/user/U12345/profile")
        assert rv.status_code == HTTP_200_OK
        assert "Slack User" in rv.text
        # Ensure get_gifts_for_user was NOT called because ID is not int
        mock_gifts.assert_not_called()
