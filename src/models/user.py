from datetime import datetime
from typing import ClassVar
from pydantic import BaseModel, Field


class InlineUser(BaseModel):
    user_id: int = 0
    name: str = ""
    usages: int = 0
    created_at: datetime | None = Field(default_factory=datetime.now)
    kind: ClassVar[str] = "InlineUser"


class User(BaseModel):
    chat_id: int = 0
    name: str = ""
    is_group: bool = False
    gdpr: bool = False
    created_at: datetime | None = Field(default_factory=datetime.now)
    kind: ClassVar[str] = "User"
