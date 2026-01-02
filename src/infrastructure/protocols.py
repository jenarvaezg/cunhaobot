from typing import Protocol, TypeVar, runtime_checkable
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from models.user import User
from models.chat import Chat
from models.usage import UsageRecord

T = TypeVar("T")


@runtime_checkable
class Repository(Protocol[T]):
    def save(self, entity: T) -> None: ...
    def delete(self, entity_id: str | int) -> None: ...
    def load(self, entity_id: str | int) -> T | None: ...
    def load_all(self) -> list[T]: ...


@runtime_checkable
class PhraseRepository(Repository[Phrase], Protocol):
    def get_phrases(
        self, search: str = "", limit: int = 0, **filters: object
    ) -> list[Phrase]: ...
    def add_usage(self, phrase_text: str, usage_type: str) -> None: ...


@runtime_checkable
class LongPhraseRepository(Repository[LongPhrase], Protocol):
    def get_phrases(
        self, search: str = "", limit: int = 0, **filters: object
    ) -> list[LongPhrase]: ...


@runtime_checkable
class ProposalRepository(Repository[Proposal], Protocol):
    def get_proposals(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: object
    ) -> list[Proposal]: ...


@runtime_checkable
class LongProposalRepository(Repository[LongProposal], Protocol):
    def get_proposals(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: object
    ) -> list[LongProposal]: ...


@runtime_checkable
class UserRepository(Repository[User], Protocol):
    def load_all(self, ignore_gdpr: bool = False) -> list[User]: ...
    def load_raw(self, entity_id: str | int) -> User | None: ...


@runtime_checkable
class ChatRepository(Repository[Chat], Protocol):
    def load_all(self) -> list[Chat]: ...


@runtime_checkable
class UsageRepository(Protocol):
    def save(self, record: UsageRecord) -> None: ...
    def get_user_usage_count(
        self, user_id: str, platform: str | None = None
    ) -> int: ...
    def get_user_action_count(self, user_id: str, action: str) -> int: ...


# Keeping it as an alias for backward compatibility in some places,
# but now it uses User model.
class InlineUserRepository(UserRepository, Protocol): ...
