from typing import Literal
from pydantic import BaseModel


class PosterRequest(BaseModel):
    id: str
    phrase: str
    user_id: int
    chat_id: int
    message_id: int | None = None
    image_url: str | None = None
    status: Literal["pending", "completed", "failed"] = "pending"
