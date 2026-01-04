from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    PHRASE = "phrase"
    STICKER = "sticker"
    SALUDO = "saludo"
    VISION = "vision"
    AI_ASK = "ai_ask"
    COMMAND = "command"
    PROPOSE = "propose"
    APPROVE = "approve"
    REJECT = "reject"
    AUDIO = "audio"
    REACTION_RECEIVED = "reaction_received"
    POSTER = "poster"
    SUBSCRIPTION = "subscription"


class UsageRecord(BaseModel):
    user_id: str
    platform: str  # "slack" | "telegram"
    action: ActionType
    phrase_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)
