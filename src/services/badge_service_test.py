import pytest
from unittest.mock import Mock, patch
from services.badge_service import BadgeService
from models.user import User
from models.usage import ActionType


@pytest.fixture
def mock_user_service():
    return Mock()


@pytest.fixture
def mock_usage_repo():
    return Mock()


@pytest.fixture
def badge_service(mock_user_service, mock_usage_repo):
    return BadgeService(u_service=mock_user_service, u_repo=mock_usage_repo)


@pytest.mark.asyncio
async def test_check_badges_awards_visionario(
    badge_service, mock_user_service, mock_usage_repo
):
    user = User(id="123", badges=[])
    mock_user_service.get_user.return_value = user

    # Mock usage counts
    # Fiera total < 50
    mock_usage_repo.get_user_usage_count.return_value = 10
    mock_usage_repo.get_recent_usage_count.return_value = 0

    # Visionario >= 10
    def side_effect(uid, p, action):
        if action == ActionType.VISION.value:
            return 10
        return 0

    mock_usage_repo.get_user_action_count.side_effect = side_effect

    # Mock phrase repo import inside the method
    with patch("infrastructure.datastore.phrase.phrase_repository") as mock_phrase_repo:
        mock_phrase_repo.get_user_phrase_count.return_value = 0

        new_badges = await badge_service.check_badges("123", "telegram")

        assert len(new_badges) == 1
        assert new_badges[0].id == "visionario"
        assert "visionario" in user.badges
        mock_user_service.save_user.assert_called_once()


@pytest.mark.asyncio
async def test_check_badges_awards_poeta(
    badge_service, mock_user_service, mock_usage_repo
):
    user = User(id="123", badges=[])
    mock_user_service.get_user.return_value = user

    mock_usage_repo.get_user_usage_count.return_value = 10
    mock_usage_repo.get_user_action_count.return_value = 0
    mock_usage_repo.get_recent_usage_count.return_value = 0

    with patch("infrastructure.datastore.phrase.phrase_repository") as mock_phrase_repo:
        mock_phrase_repo.get_user_phrase_count.return_value = 5

        new_badges = await badge_service.check_badges("123", "telegram")

        assert len(new_badges) == 1
        assert new_badges[0].id == "poeta"
        assert "poeta" in user.badges


@pytest.mark.asyncio
async def test_check_badges_awards_pesao(
    badge_service, mock_user_service, mock_usage_repo
):
    user = User(id="123", badges=[])
    mock_user_service.get_user.return_value = user

    mock_usage_repo.get_user_usage_count.return_value = 5  # Not fiera total
    mock_usage_repo.get_user_action_count.return_value = 0  # Not visionario
    mock_usage_repo.get_recent_usage_count.return_value = 10  # YES pesao

    with patch("infrastructure.datastore.phrase.phrase_repository") as mock_phrase_repo:
        mock_phrase_repo.get_user_phrase_count.return_value = 0  # Not poeta

        new_badges = await badge_service.check_badges("123", "telegram")

        assert any(b.id == "pesao" for b in new_badges)
        assert "pesao" in user.badges
