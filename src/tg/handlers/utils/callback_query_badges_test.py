import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tg.handlers.utils.callback_query import approve_proposal, dismiss_proposal
from models.proposal import Proposal
from services.badge_service import Badge


@pytest.mark.asyncio
async def test_approve_proposal_awards_badge():
    p = Proposal(id="123", text="test", from_chat_id=123, user_id="user1")
    bot = MagicMock()
    bot.send_message = AsyncMock()

    badge = Badge(id="poeta", name="Poeta", description="desc", icon="icon")

    with (
        patch(
            "tg.handlers.utils.callback_query._ensure_admins", new_callable=AsyncMock
        ),
        patch("services.proposal_repo.save", new_callable=AsyncMock),
        patch("tg.handlers.utils.callback_query.phrase_service") as mock_ph_svc,
        patch(
            "tg.handlers.utils.callback_query.get_vote_summary", return_value="summary"
        ),
        patch(
            "tg.handlers.utils.callback_query.usage_service.log_usage",
            new_callable=AsyncMock,
        ) as mock_log_usage,
    ):
        mock_ph_svc.get_random = AsyncMock()
        mock_ph_svc.get_random.return_value.text = "cuñao"
        mock_ph_svc.create_from_proposal = AsyncMock()

        # Mock that log_usage returns a new badge
        mock_log_usage.return_value = [badge]

        await approve_proposal(p, bot)

        # Check that usage was logged
        mock_log_usage.assert_called_once()

        # Check that notification message includes badge info
        assert bot.send_message.call_count == 2
        # The message to the user (from_chat_id=123) should contain badge info
        calls = bot.send_message.call_args_list
        user_call = next(c for c in calls if c[0][0] == 123)
        assert "Has desbloqueado logros" in user_call[0][1]
        assert "Poeta" in user_call[0][1]


@pytest.mark.asyncio
async def test_dismiss_proposal_awards_badge():
    p = Proposal(id="123", text="test", from_chat_id=123, user_id="user1")
    bot = MagicMock()
    bot.send_message = AsyncMock()

    badge = Badge(
        id="incomprendido", name="Incomprendido", description="desc", icon="icon"
    )

    with (
        patch(
            "tg.handlers.utils.callback_query._ensure_admins", new_callable=AsyncMock
        ),
        patch("services.proposal_repo.save", new_callable=AsyncMock),
        patch("tg.handlers.utils.callback_query.phrase_service") as mock_ph_svc,
        patch(
            "tg.handlers.utils.callback_query.get_vote_summary", return_value="summary"
        ),
        patch(
            "tg.handlers.utils.callback_query.usage_service.log_usage",
            new_callable=AsyncMock,
        ) as mock_log_usage,
    ):
        mock_ph_svc.get_random = AsyncMock()
        mock_ph_svc.get_random.return_value.text = "cuñao"

        # Mock that log_usage returns a new badge
        mock_log_usage.return_value = [badge]

        await dismiss_proposal(p, bot)

        # Check that usage was logged
        mock_log_usage.assert_called_once()

        # Check that notification message includes badge info
        assert bot.send_message.call_count == 2
        user_call = next(c for c in bot.send_message.call_args_list if c[0][0] == 123)
        assert "Has desbloqueado logros" in user_call[0][1]
        assert "Incomprendido" in user_call[0][1]
