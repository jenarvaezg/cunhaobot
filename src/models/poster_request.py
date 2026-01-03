from pydantic import BaseModel


class PosterRequest(BaseModel):
    id: str
    phrase: str
    user_id: int
    chat_id: int
    message_id: int | None = None
