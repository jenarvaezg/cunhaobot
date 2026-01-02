from datetime import datetime, timedelta
from typing import ClassVar
from pydantic import BaseModel, Field


class LinkRequest(BaseModel):
    token: str  # The unique merge code
    source_user_id: str | int
    source_platform: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(minutes=10)
    )
    kind: ClassVar[str] = "LinkRequest"
