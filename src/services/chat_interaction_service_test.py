import pytest
from unittest.mock import AsyncMock

from models.usage import ActionType
from services.chat_interaction_service import (
    AIReply,
    ChatInteractionService,
    ReactionDecision,
)


class TestChatInteractionService:
    """Telegram and Slack share the same Chat interaction product rules: an AI
    answer is an AI_ASK Uso, and a delivered smart reaction is a
    REACTION_RECEIVED Uso. The service owns that behavior so platform handlers
    only translate events and render responses."""

    @pytest.fixture
    def service(self):
        self.cunhao_agent = AsyncMock()
        self.ai_service = AsyncMock()
        self.usage_service = AsyncMock()
        return ChatInteractionService(
            cunhao_agent=self.cunhao_agent,
            ai_service=self.ai_service,
            usage_service=self.usage_service,
        )

    @pytest.mark.asyncio
    async def test_answer_logs_ai_ask_and_returns_reply(self, service):
        self.cunhao_agent.answer.return_value = "Pues mira, chaval"
        self.usage_service.log_usage.return_value = ["badge1"]

        reply = await service.answer(user_id="U1", platform="slack", text="¿qué tal?")

        assert isinstance(reply, AIReply)
        assert reply.text == "Pues mira, chaval"
        assert reply.new_badges == ["badge1"]
        self.cunhao_agent.answer.assert_awaited_once_with("¿qué tal?")
        self.usage_service.log_usage.assert_awaited_once_with(
            user_id="U1", platform="slack", action=ActionType.AI_ASK
        )

    @pytest.mark.asyncio
    async def test_decide_reaction_returns_emoji_without_logging(self, service):
        # Deciding the reaction is the shared product rule; rendering and the
        # REACTION_RECEIVED Uso happen after the platform applies it.
        self.ai_service.analyze_sentiment_and_react.return_value = "🔥"

        decision = await service.decide_reaction("menudo crack")

        assert decision == ReactionDecision(emoji="🔥")
        self.usage_service.log_usage.assert_not_called()

    @pytest.mark.asyncio
    async def test_decide_reaction_none_when_no_sentiment(self, service):
        self.ai_service.analyze_sentiment_and_react.return_value = None

        decision = await service.decide_reaction("texto neutro")

        assert decision.emoji is None

    @pytest.mark.asyncio
    async def test_record_reaction_received_logs_usage(self, service):
        self.usage_service.log_usage.return_value = ["centro_atencion"]

        badges = await service.record_reaction_received(
            user_id=123, platform="telegram"
        )

        assert badges == ["centro_atencion"]
        self.usage_service.log_usage.assert_awaited_once_with(
            user_id=123, platform="telegram", action=ActionType.REACTION_RECEIVED
        )
