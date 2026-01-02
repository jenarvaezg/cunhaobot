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
    user_repo, link_repo, phrase_repo, _, _, _ = mock_repos
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

    # Mock get_user to return source and target
    def get_user_side_effect(uid, platform=None):
        if uid == "source":
            return source_user
        if uid == "target":
            return target_user
        return None

    # Since get_user calls user_repo.load, we mock that
    # user_repo.load is mocked via service.user_repo
    user_repo.load.side_effect = (
        lambda uid: source_user if uid == "source" else target_user
    )

    # Setup phrase repo to return some items
    mock_phrase = MagicMock()
    phrase_repo.get_phrases.return_value = [mock_phrase]

    success = service.complete_link(token, "target", "slack")

    assert success is True

    # Verify Merge
    assert target_user.points == 30  # 10 + 20
    assert target_user.usages == 15  # 5 + 10
    assert set(target_user.badges) == {"b1", "b2"}

    # Verify Save Target
    assert user_repo.save.call_count >= 1
    # Actually complete_link calls save_user once for target.
    # delete_user calls save(user) (soft delete) or delete(id) (hard).
    # Code calls delete_user(..., hard=True) -> user_repo.delete(id)
    user_repo.delete.assert_called_once_with("source")

    # Verify Content Migration
    assert mock_phrase.user_id == "target"
    phrase_repo.save.assert_called_with(mock_phrase)

    # Verify Token Deletion
    # link_repo was patched in service
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
