from dataclasses import dataclass, field
from typing import ClassVar, Generic, Optional, Protocol, TypeVar, cast

from google.cloud import datastore
from telegram import Message, Update

from models.phrase import LongPhrase, Phrase
from utils import normalize_str
from utils.gcp import get_datastore_client

T = TypeVar("T", bound="Proposal")


@dataclass(unsafe_hash=True)
class Proposal:
    id: str
    from_chat_id: int
    from_message_id: int
    text: str
    liked_by: list[int] = field(default_factory=list)
    disliked_by: list[int] = field(default_factory=list)
    user_id: int = 0

    kind: ClassVar[str] = "Proposal"
    phrase_class: ClassVar[type[Phrase]] = Phrase

    @staticmethod
    def proposal_text_from_message(message: Message) -> str:
        if not (msg_text := message.text):
            return ""

        if not msg_text.startswith("/"):
            return msg_text.strip()

        # It starts with a command
        parts = msg_text.split(" ", 1)
        if len(parts) > 1:
            return parts[1].strip()

        # Just the command, check if it's a reply
        if message.reply_to_message and message.reply_to_message.text:
            return message.reply_to_message.text

        return ""

    @classmethod
    def from_update(cls: type[T], update: Update, text: str | None = None) -> T:
        if not (message := update.effective_message) or not (
            user := update.effective_user
        ):
            raise ValueError("Update has no effective message or user")

        proposal_id = str(message.chat.id + message.message_id)

        return cls(
            id=proposal_id,
            from_chat_id=message.chat.id,
            from_message_id=message.message_id,
            text=text if text is not None else cls.proposal_text_from_message(message),
            user_id=user.id,
        )

    def add_vote(self, positive: bool, voter_id: int) -> None:
        if positive:
            add_set, remove_set = set(self.liked_by), set(self.disliked_by)
        else:
            add_set, remove_set = set(self.disliked_by), set(self.liked_by)

        if voter_id in remove_set:
            remove_set.remove(voter_id)

        add_set.add(voter_id)

        # Convert back to list and assign
        if positive:
            self.liked_by, self.disliked_by = list(add_set), list(remove_set)
        else:
            self.liked_by, self.disliked_by = list(remove_set), list(add_set)

    # --- Facade / Active Record style methods ---

    @classmethod
    def get_repository(cls: type[T]) -> "ProposalRepository[T]":
        return get_repository(cls)

    def save(self) -> None:
        self.get_repository().save(self)

    def delete(self) -> None:
        self.get_repository().delete(self.id)

    @classmethod
    def load(cls: type[T], id: str) -> Optional[T]:
        return cls.get_repository().load(id)

    @classmethod
    def load_all(cls: type[T]) -> list[T]:
        return cls.get_repository().load_all()

    @classmethod
    def get_proposals(cls: type[T], search: str = "", **filters) -> list[T]:
        return cls.get_repository().get_proposals(search=search, **filters)


@dataclass(unsafe_hash=True)
class LongProposal(Proposal):
    kind: ClassVar[str] = "LongProposal"
    phrase_class: ClassVar[type[Phrase]] = LongPhrase


# --- Repository Protocol ---


class ProposalRepository(Generic[T], Protocol):
    def save(self, proposal: T) -> None: ...
    def delete(self, proposal_id: str) -> None: ...
    def load(self, proposal_id: str) -> Optional[T]: ...
    def load_all(self) -> list[T]: ...
    def get_proposals(self, search: str = "", **filters) -> list[T]: ...


# --- Datastore Implementation ---


class DatastoreProposalRepository(Generic[T]):
    def __init__(self, model_class: type[T]):
        self.model_class = model_class

    @property
    def client(self) -> datastore.Client:
        return get_datastore_client()

    def _entity_to_domain(self, entity: datastore.Entity) -> T:
        return self.model_class(
            id=entity.key.name,
            from_chat_id=entity["from_chat_id"],
            from_message_id=entity["from_message_id"],
            text=entity["text"],
            liked_by=list(entity.get("liked_by", [])),
            disliked_by=list(entity.get("disliked_by", [])),
            user_id=entity.get("user_id", 0),
        )

    def _domain_to_entity(self, proposal: T, key: datastore.Key) -> datastore.Entity:
        entity = datastore.Entity(key=key)
        entity.update(
            {
                "text": proposal.text,
                "from_chat_id": proposal.from_chat_id,
                "from_message_id": proposal.from_message_id,
                "liked_by": proposal.liked_by,
                "disliked_by": proposal.disliked_by,
                "user_id": proposal.user_id,
            }
        )
        return entity

    def save(self, proposal: T) -> None:
        client = self.client
        key = client.key(self.model_class.kind, proposal.id)
        entity = self._domain_to_entity(proposal, key)
        client.put(entity)

    def delete(self, proposal_id: str) -> None:
        client = self.client
        key = client.key(self.model_class.kind, proposal_id)
        client.delete(key)

    def load(self, proposal_id: str) -> Optional[T]:
        client = self.client
        key = client.key(self.model_class.kind, proposal_id)
        entity = client.get(key)
        if entity is None:
            return None
        return self._entity_to_domain(entity)

    def load_all(self) -> list[T]:
        client = self.client
        query = client.query(kind=self.model_class.kind)
        return [self._entity_to_domain(entity) for entity in query.fetch()]

    def get_proposals(self, search: str = "", **filters) -> list[T]:
        results = self.load_all()

        if search:
            normalized_search = normalize_str(search)
            results = [p for p in results if normalized_search in normalize_str(p.text)]

        for field_name, value in filters.items():
            if not value:
                continue

            if value == "__EMPTY__":
                results = [p for p in results if not getattr(p, field_name, None)]
            else:
                results = [
                    p
                    for p in results
                    if str(getattr(p, field_name, None)) == str(value)
                ]

        return results


# --- Dependency Injection / Singleton ---

_proposal_repository: DatastoreProposalRepository[Proposal] = (
    DatastoreProposalRepository(Proposal)
)
_long_proposal_repository: DatastoreProposalRepository[LongProposal] = (
    DatastoreProposalRepository(LongProposal)
)


def get_repository(model_class: type[T]) -> ProposalRepository[T]:
    if issubclass(model_class, LongProposal):
        return cast(ProposalRepository[T], _long_proposal_repository)
    return cast(ProposalRepository[T], _proposal_repository)


def get_proposal_class_by_kind(kind: str) -> type[Proposal]:
    if kind == LongProposal.kind:
        return LongProposal
    return Proposal
