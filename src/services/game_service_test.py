import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from services.game_service import GamePlayerProfile, GameService
from models.user import User


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: dict[str | int, User] = {}
        self.saved: list[User] = []

    async def save(self, entity: User) -> None:
        self.users[entity.id] = entity
        self.saved.append(entity)

    async def delete(self, entity_id: str | int) -> None:
        self.users.pop(entity_id, None)

    async def load(self, entity_id: str | int) -> User | None:
        return self.users.get(entity_id)

    async def load_all(self, ignore_gdpr: bool = False) -> list[User]:
        return list(self.users.values())

    def clear_cache(self) -> None:
        return None

    async def load_raw(self, entity_id: str | int) -> User | None:
        return await self.load(entity_id)

    async def get_by_username(self, username: str) -> User | None:
        return next(
            (user for user in self.users.values() if user.username == username),
            None,
        )


@pytest.mark.asyncio
async def test_process_score_success():
    mock_user_repo = AsyncMock()
    mock_badge_service = AsyncMock()
    service = GameService(mock_user_repo, mock_badge_service)

    user_id = "123"
    score = 550

    mock_user = MagicMock()
    mock_user.points = 1000
    mock_user.game_stats = 0
    mock_user.game_high_score = 0
    mock_user.game_streak = 0
    mock_user.last_game_at = None
    mock_user.platform = "telegram"

    mock_user_repo.load.return_value = mock_user

    with patch(
        "tg.get_initialized_tg_application", new_callable=AsyncMock
    ) as mock_tg_app:
        mock_bot = AsyncMock()
        mock_tg_app.return_value.bot = mock_bot

        result = await service.set_score(user_id, score, "inline_id")

        assert result is True
        assert mock_user.points == 1005  # 1000 + 550//100
        assert mock_user.game_stats == 1
        assert mock_user.game_high_score == 550
        assert mock_user.game_streak == 1
        assert mock_user.last_game_at is not None

        mock_user_repo.save.assert_called_once_with(mock_user)
        mock_badge_service.check_badges.assert_called_once_with(user_id, "telegram")
        mock_bot.set_game_score.assert_called_once_with(
            user_id=123, score=550, inline_message_id="inline_id"
        )


@pytest.mark.asyncio
async def test_process_score_streak():
    mock_user_repo = AsyncMock()
    mock_badge_service = AsyncMock()
    service = GameService(mock_user_repo, mock_badge_service)

    user_id = "123"

    # Last game was yesterday
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    mock_user = MagicMock()
    mock_user.points = 0
    mock_user.game_stats = 10
    mock_user.game_high_score = 100
    mock_user.game_streak = 5
    mock_user.last_game_at = yesterday
    mock_user.platform = "telegram"

    mock_user_repo.load.return_value = mock_user

    with patch("tg.get_initialized_tg_application", new_callable=AsyncMock):
        await service.set_score(user_id, 100)
        assert mock_user.game_streak == 6


@pytest.mark.asyncio
async def test_submit_score_creates_matching_web_profile_before_saving_score():
    user_repo = InMemoryUserRepository()
    badge_service = AsyncMock()
    badge_service.check_badges.return_value = []
    service = GameService(user_repo, badge_service)
    token = service.generate_game_token("123")

    with patch("tg.get_initialized_tg_application", new_callable=AsyncMock):
        result = await service.submit_score(
            user_id="123",
            score=450,
            token=token,
            player_profile=GamePlayerProfile(
                user_id="123",
                name="Web Player",
                username="web_player",
            ),
        )

    assert result is True
    stored_user = user_repo.users["123"]
    assert stored_user.name == "Web Player"
    assert stored_user.username == "web_player"
    assert stored_user.points == 4
    assert stored_user.game_stats == 1
    assert stored_user.game_high_score == 450
