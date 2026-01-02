from datetime import datetime
from typing import ClassVar
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str | int = 0
    platform: str = "telegram"
    name: str = ""
    username: str | None = None
    is_group: bool = False
    is_private: bool = False
    gdpr: bool = False
    usages: int = 0
    points: int = 0
    badges: list[str] = Field(default_factory=list)
    last_usages: list[datetime] = Field(default_factory=list)
    created_at: datetime | None = Field(default_factory=datetime.now)
    kind: ClassVar[str] = "User"
