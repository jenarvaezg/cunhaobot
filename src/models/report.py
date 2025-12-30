from datetime import datetime
from typing import ClassVar
from pydantic import BaseModel, Field


class Report(BaseModel):
    longs: int
    shorts: int
    users: int
    groups: int
    inline_users: int
    inline_usages: int
    gdprs: int
    chapas: int
    top_long: str
    top_short: str
    created_at: datetime | None = Field(default_factory=datetime.now)

    kind: ClassVar[str] = "Report"

    @property
    def datastore_id(self) -> str:
        if self.created_at is None:
            return "unknown"
        return self.created_at.strftime("%Y/%m/%d")
