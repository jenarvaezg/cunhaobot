from typing import Protocol, TypeVar, Any, runtime_checkable
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from models.user import User

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
        self, search: str = "", limit: int = 0, **filters: Any
    ) -> list[Phrase]: ...
    def add_usage(self, phrase_text: str, usage_type: str) -> None: ...


@runtime_checkable
class LongPhraseRepository(Repository[LongPhrase], Protocol):
    def get_phrases(
        self, search: str = "", limit: int = 0, **filters: Any
    ) -> list[LongPhrase]: ...


@runtime_checkable
class ProposalRepository(Repository[Proposal], Protocol):
    def get_proposals(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: Any
    ) -> list[Proposal]: ...


@runtime_checkable
class LongProposalRepository(Repository[LongProposal], Protocol):
    def get_proposals(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: Any
    ) -> list[LongProposal]: ...


@runtime_checkable
class UserRepository(Repository[User], Protocol):
    def load_all(self, ignore_gdpr: bool = False) -> list[User]: ...


# Keeping it as an alias for backward compatibility in some places,
# but now it uses User model.
class InlineUserRepository(UserRepository, Protocol): ...
