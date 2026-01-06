import pytest
from unittest.mock import AsyncMock
from models.user import User
from services.user_service import UserService


@pytest.mark.asyncio
async def test_update_or_create_slack_user():
    user_repo = AsyncMock()
    user_repo.load.return_value = None
    service = UserService(
        user_repo=user_repo,
        chat_repo=AsyncMock(),
        phrase_repo=AsyncMock(),
        long_phrase_repo=AsyncMock(),
        proposal_repo=AsyncMock(),
        long_proposal_repo=AsyncMock(),
        link_request_repo=AsyncMock(),
    )

    user = await service.update_or_create_slack_user(
        slack_user_id="U123456", name="Slack User", username="slackuser"
    )

    assert user.id == "U123456"
    assert user.name == "Slack User"
    assert user.username == "slackuser"
    assert user.platform == "slack"
    user_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_update_slack_user_existing():
    existing_user = User(id="U123456", name="Old Name", platform="slack")
    user_repo = AsyncMock()
    user_repo.load.return_value = existing_user
    service = UserService(
        user_repo=user_repo,
        chat_repo=AsyncMock(),
        phrase_repo=AsyncMock(),
        long_phrase_repo=AsyncMock(),
        proposal_repo=AsyncMock(),
        long_proposal_repo=AsyncMock(),
        link_request_repo=AsyncMock(),
    )

    user = await service.update_or_create_slack_user(
        slack_user_id="U123456", name="New Name", username="newuser"
    )

    assert user.id == "U123456"
    assert user.name == "New Name"
    assert user.username == "newuser"
    assert user.platform == "slack"
    user_repo.save.assert_called_once()
