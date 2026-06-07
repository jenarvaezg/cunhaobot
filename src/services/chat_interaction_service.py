"""Shared Chat interaction behavior across platform adapters.

Telegram and Slack apply the same product rules when Cunhaobot talks in a
Chat: an AI answer counts as an AI_ASK Uso, and a delivered smart reaction
counts as a REACTION_RECEIVED Uso. This module owns those rules so the
platform handlers only translate events and render the response/reaction in
their own SDK.

Premium gating is intentionally NOT here: it varies by platform (currently
Telegram-only), and a seam is only introduced where behavior is shared.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from models.usage import ActionType

if TYPE_CHECKING:
    from services.cunhao_agent import CunhaoAgent
    from services.ai_service import AIService
    from services.usage_service import UsageService
    from services.badge_service import Badge


@dataclass(frozen=True)
class AIReply:
    """An AI answer plus any Logros unlocked by logging the AI_ASK Uso."""

    text: str
    new_badges: "list[Badge]" = field(default_factory=list)


@dataclass(frozen=True)
class ReactionDecision:
    """The smart-reaction emoji to apply, or None when no reaction is warranted."""

    emoji: str | None = None


class ChatInteractionService:
    def __init__(
        self,
        cunhao_agent: "CunhaoAgent",
        ai_service: "AIService",
        usage_service: "UsageService",
    ):
        self.cunhao_agent = cunhao_agent
        self.ai_service = ai_service
        self.usage_service = usage_service

    async def answer(self, *, user_id: str | int, platform: str, text: str) -> AIReply:
        """Produce the AI answer for a Chat message and record the AI_ASK Uso."""
        response = await self.cunhao_agent.answer(text)
        new_badges = await self.usage_service.log_usage(
            user_id=user_id, platform=platform, action=ActionType.AI_ASK
        )
        return AIReply(text=response, new_badges=new_badges or [])

    async def decide_reaction(self, text: str) -> ReactionDecision:
        """Decide which smart reaction (if any) a Chat message warrants.

        The Uso is only recorded once the platform actually delivers the
        reaction, via :meth:`record_reaction_received`.
        """
        emoji = await self.ai_service.analyze_sentiment_and_react(text)
        return ReactionDecision(emoji=emoji or None)

    async def record_reaction_received(
        self, *, user_id: str | int, platform: str
    ) -> "list[Badge]":
        """Record a delivered smart reaction as a REACTION_RECEIVED Uso."""
        new_badges = await self.usage_service.log_usage(
            user_id=user_id, platform=platform, action=ActionType.REACTION_RECEIVED
        )
        return new_badges or []
