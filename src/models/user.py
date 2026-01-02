from datetime import datetime, timezone
from typing import ClassVar
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str | int = 0
    platform: str = "telegram"
    name: str = ""
    username: str | None = None
    is_private: bool = False
    gdpr: bool = False
    usages: int = 0
    points: int = 0
    badges: list[str] = Field(default_factory=list)
    linked_to: str | int | None = None
    last_usages: list[datetime] = Field(default_factory=list)
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    kind: ClassVar[str] = "User"
