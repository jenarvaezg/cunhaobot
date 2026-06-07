import pytest
from unittest.mock import AsyncMock

from models.user import User
from models.phrase import Phrase, LongPhrase
from services.badge_service import Badge, BadgeProgress
from services.profile_service import ProfileService, ProfileSummary


def _progress(badge_id: str, is_earned: bool) -> BadgeProgress:
    return BadgeProgress(
        badge=Badge(id=badge_id, name=badge_id.title(), description="", icon="🏅"),
        is_earned=is_earned,
        progress=100 if is_earned else 0,
        current=1 if is_earned else 0,
        target=1,
    )


class TestProfileService:
    """Profile aggregation sits behind one interface so web, Telegram and Slack
    profile views consume a coherent Perfil summary instead of reassembling
    Puntos de reputación, Logros, Pieza cuñadil, Regalos and Pósters
    independently."""

    @pytest.fixture
    def service(self):
        self.phrase_repo = AsyncMock()
        self.long_phrase_repo = AsyncMock()
        self.gift_repo = AsyncMock()
        self.poster_request_repo = AsyncMock()
        self.badge_service = AsyncMock()
        self.usage_service = AsyncMock()
        return ProfileService(
            phrase_repo=self.phrase_repo,
            long_phrase_repo=self.long_phrase_repo,
            gift_repo=self.gift_repo,
            poster_request_repo=self.poster_request_repo,
            badge_service=self.badge_service,
            usage_service=self.usage_service,
        )

    def _setup(self, *, phrases, long_phrases, posters, gifts, badges_progress, usages):
        self.phrase_repo.get_phrases.return_value = phrases
        self.long_phrase_repo.get_phrases.return_value = long_phrases
        self.poster_request_repo.get_completed_by_user.return_value = posters
        self.gift_repo.get_gifts_for_user.return_value = gifts
        self.badge_service.get_all_badges_progress.return_value = badges_progress
        self.usage_service.get_user_stats.return_value = {"total_usages": usages}

    @pytest.mark.asyncio
    async def test_aggregates_a_coherent_summary(self, service):
        earned = _progress("poeta", True)
        unearned = _progress("vip", False)
        poster = object()
        gift = object()
        self._setup(
            phrases=[Phrase(id=1, text="cuñado", usages=2)],
            long_phrases=[LongPhrase(id=2, text="frase larga", usages=9)],
            posters=[poster],
            gifts=[gift],
            badges_progress=[earned, unearned],
            usages=42,
        )

        user = User(id="100", platform="telegram", points=250)
        summary = await service.get_profile_summary(user)

        assert isinstance(summary, ProfileSummary)
        assert summary.user is user
        assert summary.points == 250
        assert summary.stats["total_usages"] == 42
        assert summary.posters == [poster]
        assert summary.gifts == [gift]
        assert summary.badges_progress == [earned, unearned]
        # Only earned Logros are surfaced as awarded badges.
        assert [b.id for b in summary.earned_badges] == ["poeta"]
        # Level grows every 100 Puntos de reputación.
        assert summary.level == 3

    @pytest.mark.asyncio
    async def test_pieces_combine_apelativo_and_frase_sorted_by_usage(self, service):
        self._setup(
            phrases=[Phrase(id=1, text="a", usages=2)],
            long_phrases=[LongPhrase(id=2, text="b", usages=9)],
            posters=[],
            gifts=[],
            badges_progress=[],
            usages=0,
        )

        user = User(id="100", platform="telegram", points=0)
        summary = await service.get_profile_summary(user)

        # Apelativo and Frase cuñadil are merged and ordered by usage desc.
        assert [p.id for p in summary.pieces] == [2, 1]
        assert summary.pieces_count == 2

    @pytest.mark.asyncio
    async def test_non_numeric_id_yields_no_gifts(self, service):
        self._setup(
            phrases=[],
            long_phrases=[],
            posters=[],
            gifts=[],
            badges_progress=[],
            usages=0,
        )

        # Slack Perfiles have non-numeric ids; Regalo lookup must not blow up.
        user = User(id="U123ABC", platform="slack", points=0)
        summary = await service.get_profile_summary(user)

        assert summary.gifts == []
        self.gift_repo.get_gifts_for_user.assert_not_called()
