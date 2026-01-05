from enum import StrEnum
from datetime import datetime, timezone
from typing import ClassVar
from pydantic import BaseModel, Field


class GiftType(StrEnum):
    PALILLO = "palillo"
    CARAJILLO = "carajillo"
    COGNAC = "cognac"
    PURO = "puro"


GIFT_PRICES = {
    GiftType.PALILLO: 1,
    GiftType.CARAJILLO: 5,
    GiftType.COGNAC: 10,
    GiftType.PURO: 25,
}

GIFT_EMOJIS = {
    GiftType.PALILLO: "🦷",
    GiftType.CARAJILLO: "☕️",
    GiftType.COGNAC: "🥃",
    GiftType.PURO: "🚬",
}

GIFT_NAMES = {
    GiftType.PALILLO: "Palillo",
    GiftType.CARAJILLO: "Carajillo",
    GiftType.COGNAC: "Copa de Coñac",
    GiftType.PURO: "Puro",
}


class Gift(BaseModel):
    id: str | int | None = None
    sender_id: int
    sender_name: str
    receiver_id: int
    gift_type: GiftType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cost: int
    kind: ClassVar[str] = "Gift"
