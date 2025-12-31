from datetime import datetime
from typing import ClassVar
from pydantic import BaseModel, Field
from models.phrase import Phrase, LongPhrase


class Proposal(BaseModel):
    id: str = ""
    from_chat_id: str | int = 0
    from_message_id: str | int = 0
    text: str = ""
    liked_by: list[str] = []
    disliked_by: list[str] = []
    user_id: str | int = 0
    voting_ended: bool = False
    voting_ended_at: datetime | None = None
    created_at: datetime | None = Field(default_factory=datetime.now)

    kind: ClassVar[str] = "Proposal"
    phrase_class: ClassVar[type[Phrase]] = Phrase


class LongProposal(Proposal):
    kind: ClassVar[str] = "LongProposal"
    phrase_class: ClassVar[type[Phrase]] = LongPhrase


def get_proposal_class_by_kind(kind: str) -> type[Proposal]:
    if kind == LongProposal.kind:
        return LongProposal
    return Proposal
