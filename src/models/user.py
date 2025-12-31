from datetime import datetime
from typing import ClassVar
from pydantic import BaseModel, Field


class User(BaseModel):
    id: int = 0
    name: str = ""
    username: str | None = None
    is_group: bool = False
    gdpr: bool = False
    usages: int = 0
    points: int = 0
    created_at: datetime | None = Field(default_factory=datetime.now)
    kind: ClassVar[str] = "User"
