from typing import Protocol, TypeVar, runtime_checkable
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from models.user import User
from models.chat import Chat
from models.usage import UsageRecord
from models.gift import Gift

T = TypeVar("T")


@runtime_checkable
class Repository(Protocol[T]):
    async def save(self, entity: T) -> None: ...
    async def delete(self, entity_id: str | int) -> None: ...
    async def load(self, entity_id: str | int) -> T | None: ...
    async def load_all(self) -> list[T]: ...


@runtime_checkable
class GiftRepository(Repository[Gift], Protocol):
    async def get_gifts_for_user(self, user_id: int) -> list[Gift]: ...


@runtime_checkable
class PhraseRepository(Repository[Phrase], Protocol):
    async def get_phrases(
        self, search: str = "", limit: int = 0, **filters: object
    ) -> list[Phrase]: ...
    async def add_usage(self, phrase_text: str, usage_type: str) -> None: ...


@runtime_checkable
class LongPhraseRepository(Repository[LongPhrase], Protocol):
    async def get_phrases(
        self, search: str = "", limit: int = 0, **filters: object
    ) -> list[LongPhrase]: ...


@runtime_checkable
class ProposalRepository(Repository[Proposal], Protocol):
    async def get_proposals(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: object
    ) -> list[Proposal]: ...


@runtime_checkable
class LongProposalRepository(Repository[LongProposal], Protocol):
    async def get_proposals(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: object
    ) -> list[LongProposal]: ...


@runtime_checkable
class UserRepository(Repository[User], Protocol):
    async def load_all(self, ignore_gdpr: bool = False) -> list[User]: ...
    async def load_raw(self, entity_id: str | int) -> User | None: ...


@runtime_checkable
class ChatRepository(Repository[Chat], Protocol):
    async def load_all(self) -> list[Chat]: ...


@runtime_checkable
class UsageRepository(Protocol):
    async def save(self, record: UsageRecord) -> None: ...
    async def get_user_usage_count(
        self, user_id: str, platform: str | None = None
    ) -> int: ...
    async def get_user_action_count(self, user_id: str, action: str) -> int: ...


# Keeping it as an alias for backward compatibility in some places,
# but now it uses User model.
class InlineUserRepository(UserRepository, Protocol): ...
