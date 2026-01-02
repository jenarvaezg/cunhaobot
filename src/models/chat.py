from datetime import datetime, timezone
from typing import ClassVar
from pydantic import BaseModel, Field


class Chat(BaseModel):
    id: str | int = 0
    platform: str = "telegram"
    title: str = ""
    username: str | None = None
    type: str = "private"  # private, group, supergroup, channel
    usages: int = 0
    is_active: bool = True
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_seen_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    kind: ClassVar[str] = "Chat"
