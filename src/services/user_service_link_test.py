import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from models.user import User
from models.link_request import LinkRequest
from services.user_service import UserService


@pytest.fixture
def mock_repos():
    with (
        patch("services.user_service.user_repository") as user_repo,
        patch("services.user_service.link_request_repository") as link_repo,
        patch("services.user_service.phrase_repository") as phrase_repo,
        patch("services.user_service.long_phrase_repository") as long_phrase_repo,
        patch("services.user_service.proposal_repository") as proposal_repo,
        patch("services.user_service.long_proposal_repository") as long_proposal_repo,
    ):
        yield (
            user_repo,
            link_repo,
            phrase_repo,
            long_phrase_repo,
            proposal_repo,
            long_proposal_repo,
        )


def test_generate_link_token(mock_repos):
    user_repo, link_repo, _, _, _, _ = mock_repos
    service = UserService(user_repo=user_repo)

    token = service.generate_link_token("user1", "telegram")

    assert len(token) == 6
    link_repo.save.assert_called_once()
    saved_request = link_repo.save.call_args[0][0]
    assert saved_request.token == token
    assert saved_request.source_user_id == "user1"
    assert saved_request.source_platform == "telegram"


def test_complete_link_success(mock_repos):
    (
        user_repo,
        link_repo,
        phrase_repo,
        long_phrase_repo,
        proposal_repo,
        long_proposal_repo,
    ) = mock_repos
    service = UserService(user_repo=user_repo)

    # Setup Data
    token = "ABCDEF"
    source_user = User(
        id="source", platform="telegram", points=10, usages=5, badges=["b1"]
    )
    target_user = User(
        id="target", platform="slack", points=20, usages=10, badges=["b2"]
    )

    request = LinkRequest(
        token=token, source_user_id="source", source_platform="telegram"
    )

    link_repo.load.return_value = request

    # Setup repo load methods
    def load_side_effect(uid, follow_link=True):
        if uid == "source":
            return source_user
        if uid == "target":
            return target_user
        return None

    user_repo.load.side_effect = load_side_effect
    user_repo.load_raw.side_effect = lambda uid: load_side_effect(
        uid, follow_link=False
    )

    # Setup phrase repo to return some items
    mock_phrase = MagicMock()
    phrase_repo.get_phrases.return_value = [mock_phrase]
    long_phrase_repo.get_phrases.return_value = []
    proposal_repo.get_phrases.return_value = []
    long_proposal_repo.get_phrases.return_value = []

    success = service.complete_link(token, "target", "slack")

    assert success is True

    # Verify Merge on Target
    assert target_user.points == 30  # 10 + 20
    assert target_user.usages == 15  # 5 + 10
    assert set(target_user.badges) == {"b1", "b2"}

    # Verify Alias on Source
    assert source_user.linked_to == "target"
    assert source_user.points == 0
    assert source_user.usages == 0
    assert source_user.badges == []

    # Verify Save calls
    # Should save target_user and then source_user
    assert user_repo.save.call_count >= 2

    # Verify no deletion
    user_repo.delete.assert_not_called()

    # Verify Content Migration
    assert mock_phrase.user_id == "target"
    phrase_repo.save.assert_called_with(mock_phrase)

    # Verify Token Deletion
    link_repo.delete.assert_called_with(token)


def test_complete_link_expired(mock_repos):
    user_repo, link_repo, _, _, _, _ = mock_repos
    service = UserService(user_repo=user_repo)

    token = "ABCDEF"
    request = LinkRequest(
        token=token,
        source_user_id="source",
        source_platform="telegram",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    link_repo.load.return_value = request

    success = service.complete_link(token, "target", "slack")

    assert success is False
    link_repo.delete.assert_called_with(token)


def test_complete_link_same_user(mock_repos):
    user_repo, link_repo, _, _, _, _ = mock_repos
    service = UserService(user_repo=user_repo)

    token = "ABCDEF"
    request = LinkRequest(token=token, source_user_id="u1", source_platform="telegram")
    link_repo.load.return_value = request

    success = service.complete_link(token, "u1", "telegram")
    assert success is False
