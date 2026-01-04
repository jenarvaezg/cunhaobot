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
    premium_until: datetime | None = None
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_seen_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    kind: ClassVar[str] = "Chat"

    @property
    def is_premium(self) -> bool:
        if not self.premium_until:
            return False
        # Ensure comparison is timezone-aware
        now = datetime.now(timezone.utc)
        if self.premium_until.tzinfo is None:
            # If stored without timezone (naive), assume UTC or force it
            self.premium_until = self.premium_until.replace(tzinfo=timezone.utc)
        return self.premium_until > now
