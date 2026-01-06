import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock
from services.badge_service import BadgeService
from models.user import User
from models.usage import ActionType


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_usage_repo():
    return AsyncMock()


@pytest.fixture
def mock_phrase_repo():
    return AsyncMock()


@pytest.fixture
def mock_long_phrase_repo():
    return AsyncMock()


@pytest.fixture
def mock_gift_repo():
    return AsyncMock()


@pytest.fixture
def badge_service(
    mock_user_repo,
    mock_usage_repo,
    mock_phrase_repo,
    mock_long_phrase_repo,
    mock_gift_repo,
):
    svc = BadgeService(
        user_repo=mock_user_repo,
        usage_repo=mock_usage_repo,
        phrase_repo=mock_phrase_repo,
        long_phrase_repo=mock_long_phrase_repo,
        gift_repo=mock_gift_repo,
    )
    # Mock the lazy user_service property
    with patch.object(BadgeService, "user_service", new_callable=MagicMock):
        svc._user_service = AsyncMock()
        return svc


@pytest.mark.asyncio
async def test_check_badges_awards_novato(badge_service, mock_usage_repo):
    user = User(id="123", badges=[])
    badge_service.user_service.get_user.return_value = user

    mock_usage_repo.get_user_usage_count.return_value = 1
    mock_usage_repo.get_user_action_count.return_value = 0
    badge_service.phrase_repo.get_user_phrase_count.return_value = 0

    new_badges = await badge_service.check_badges("123", "telegram")

    assert any(b.id == "novato" for b in new_badges)
    assert "novato" in user.badges


@pytest.mark.asyncio
async def test_check_badges_awards_visionario(badge_service, mock_usage_repo):
    # User already has novato
    user = User(id="123", badges=["novato"])
    badge_service.user_service.get_user.return_value = user

    # Mock usage counts
    # Fiera total < 50
    mock_usage_repo.get_user_usage_count.return_value = 10

    # Visionario >= 5
    async def side_effect(uid, platform=None, action=None):
        if action == ActionType.VISION.value:
            return 10
        return 0

    mock_usage_repo.get_user_action_count.side_effect = side_effect
    badge_service.phrase_repo.get_user_phrase_count.return_value = 0

    new_badges = await badge_service.check_badges("123", "telegram")

    assert any(b.id == "visionario" for b in new_badges)
    assert "visionario" in user.badges
    badge_service.user_service.save_user.assert_called_once()


@pytest.mark.asyncio
async def test_check_badges_awards_poeta(badge_service, mock_usage_repo):
    # User already has novato
    user = User(id="123", badges=["novato"])
    badge_service.user_service.get_user.return_value = user

    mock_usage_repo.get_user_usage_count.return_value = 10
    mock_usage_repo.get_user_action_count.return_value = 0

    badge_service.phrase_repo.get_user_phrase_count.return_value = 5

    new_badges = await badge_service.check_badges("123", "telegram")

    assert any(b.id == "poeta" for b in new_badges)
    assert "poeta" in user.badges


@pytest.mark.asyncio
async def test_check_badges_awards_pesao(badge_service, mock_usage_repo):
    # Setup user with 9 recent usages (current interaction will make it 10)
    # User already has novato
    now = datetime.now(timezone.utc)
    user = User(id="123", badges=["novato"], last_usages=[now] * 9)
    badge_service.user_service.get_user.return_value = user

    mock_usage_repo.get_user_usage_count.return_value = 5  # Not fiera total
    mock_usage_repo.get_user_action_count.return_value = 0  # Not visionario

    badge_service.phrase_repo.get_user_phrase_count.return_value = 0  # Not poeta

    new_badges = await badge_service.check_badges("123", "telegram")

    assert any(b.id == "pesao" for b in new_badges)
    assert "pesao" in user.badges
    assert len(user.last_usages) == 10
    badge_service.user_service.save_user.assert_called_once()
