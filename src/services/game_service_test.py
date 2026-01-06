import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from services.game_service import GameService


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

    with patch("services.game_service.get_tg_application") as mock_tg_app:
        mock_bot = AsyncMock()
        mock_tg_app.return_value.bot = mock_bot
        mock_tg_app.return_value.running = True

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

    with patch("services.game_service.get_tg_application"):
        await service.set_score(user_id, 100)
        assert mock_user.game_streak == 6
