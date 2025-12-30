from datetime import datetime
from typing import ClassVar
from pydantic import BaseModel


class Phrase(BaseModel):
    key: str = ""
    text: str = ""
    sticker_file_id: str = ""
    usages: int = 0
    audio_usages: int = 0
    daily_usages: int = 0
    audio_daily_usages: int = 0
    sticker_usages: int = 0
    sticker_daily_usages: int = 0
    user_id: int = 0
    chat_id: int = 0
    created_at: datetime | None = None
    proposal_id: str = ""

    # Constants
    kind: ClassVar[str] = "Phrase"
    display_name: ClassVar[str] = "palabra poderosa / apelativo"
    name: ClassVar[str] = "palabra poderosa / apelativo"
    stickerset_template: ClassVar[str] = "greeting_{}_by_cunhaobot"
    stickerset_title_template: ClassVar[str] = "Saludos cuñadiles {} by @cunhaobot"

    def __str__(self) -> str:
        return self.text

    def __hash__(self) -> int:
        return hash((self.text, self.kind))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Phrase):
            return False
        return self.text == other.text and self.kind == other.kind


class LongPhrase(Phrase):
    kind: ClassVar[str] = "LongPhrase"
    display_name: ClassVar[str] = "frase / dicho cuñadíl"
    name: ClassVar[str] = "frase / dicho cuñadíl"
    stickerset_template: ClassVar[str] = "phrase_{}_by_cunhaobot"
    stickerset_title_template: ClassVar[str] = "Frases cuñadiles {} by @cunhaobot"
