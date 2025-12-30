from datetime import datetime
from typing import ClassVar
from pydantic import BaseModel, Field


class Schedule(BaseModel):
    id: str = ""
    chat_id: int
    user_id: int = 0
    hour: int
    minute: int
    query: str = ""
    service: str = "telegram"
    task_type: str = "chapa"
    active: bool = True
    created_at: datetime | None = Field(default_factory=datetime.now)
    kind: ClassVar[str] = "Schedule"
