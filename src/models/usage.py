from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    PHRASE = "phrase"
    STICKER = "sticker"
    SALUDO = "saludo"
    VISION = "vision"
    AI_ASK = "ai_ask"
    COMMAND = "command"


class UsageRecord(BaseModel):
    user_id: str
    platform: str  # "slack" | "telegram"
    action: ActionType
    phrase_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
