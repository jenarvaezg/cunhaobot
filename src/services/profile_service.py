"""Perfil aggregation.

Web, Telegram and Slack profile views all need the same coherent Perfil
summary: Puntos de reputación, Logros, authored Pieza cuñadil, Regalos and
Pósters. This module assembles that summary once so callers stop rebuilding
the same statistics in different ways.
"""

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from models.user import User
from models.phrase import Phrase

if TYPE_CHECKING:
    from infrastructure.protocols import (
        PhraseRepository,
        LongPhraseRepository,
        GiftRepository,
        PosterRequestRepository,
    )
    from models.gift import Gift
    from models.poster_request import PosterRequest
    from services.badge_service import Badge, BadgeProgress, BadgeService
    from services.usage_service import UsageService


@dataclass(frozen=True)
class ProfileSummary:
    """A coherent snapshot of a Perfil for any profile presentation."""

    user: User
    stats: dict[str, int]
    badges_progress: "list[BadgeProgress]"
    pieces: list[Phrase]
    posters: "list[PosterRequest]"
    gifts: "list[Gift]"
    level: int

    @property
    def points(self) -> int:
        return self.user.points

    @property
    def earned_badges(self) -> "list[Badge]":
        return [p.badge for p in self.badges_progress if p.is_earned]

    @property
    def pieces_count(self) -> int:
        return len(self.pieces)


class ProfileService:
    def __init__(
        self,
        phrase_repo: "PhraseRepository",
        long_phrase_repo: "LongPhraseRepository",
        gift_repo: "GiftRepository",
        poster_request_repo: "PosterRequestRepository",
        badge_service: "BadgeService",
        usage_service: "UsageService",
    ):
        self.phrase_repo = phrase_repo
        self.long_phrase_repo = long_phrase_repo
        self.gift_repo = gift_repo
        self.poster_request_repo = poster_request_repo
        self.badge_service = badge_service
        self.usage_service = usage_service

    async def get_profile_summary(self, user: User) -> ProfileSummary:
        """Aggregate the canonical Perfil summary for a resolved Perfil."""
        user_key = str(user.id)
        (
            stats,
            badges_progress,
            phrases,
            long_phrases,
            posters,
            gifts,
        ) = await asyncio.gather(
            self.usage_service.get_user_stats(user.id),
            self.badge_service.get_all_badges_progress(
                user.id, user.platform, user=user
            ),
            self.phrase_repo.get_phrases(user_id=user_key),
            self.long_phrase_repo.get_phrases(user_id=user_key),
            self.poster_request_repo.get_completed_by_user(user.id),
            self._gifts_for(user),
        )

        # Apelativo and Frase cuñadil share one repertory in the summary.
        pieces = sorted([*phrases, *long_phrases], key=lambda p: p.usages, reverse=True)
        level = 1 + int(user.points / 100)

        return ProfileSummary(
            user=user,
            stats=stats,
            badges_progress=badges_progress,
            pieces=pieces,
            posters=posters,
            gifts=gifts,
            level=level,
        )

    async def _gifts_for(self, user: User) -> "list[Gift]":
        # Regalos are keyed by numeric id; Slack Perfiles have non-numeric ids.
        try:
            numeric_id = int(user.id)
        except TypeError, ValueError:
            return []
        return await self.gift_repo.get_gifts_for_user(numeric_id)
