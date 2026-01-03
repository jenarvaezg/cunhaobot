from typing import cast
from infrastructure.protocols import (
    PhraseRepository,
    LongPhraseRepository,
    ProposalRepository,
    LongProposalRepository,
    UserRepository,
    ChatRepository,
    UsageRepository,
)
from infrastructure.datastore.phrase import phrase_repository, long_phrase_repository
from infrastructure.datastore.proposal import (
    proposal_repository,
    long_proposal_repository,
)
from infrastructure.datastore.user import user_repository
from infrastructure.datastore.usage import usage_repository
from infrastructure.datastore.chat import chat_repository
from infrastructure.datastore.poster_request import poster_request_repository

# Alias with explicit protocol casting
phrase_repo = cast(PhraseRepository, phrase_repository)
long_phrase_repo = cast(LongPhraseRepository, long_phrase_repository)
proposal_repo = cast(ProposalRepository, proposal_repository)
long_proposal_repo = cast(LongProposalRepository, long_proposal_repository)
user_repo = cast(UserRepository, user_repository)
usage_repo = cast(UsageRepository, usage_repository)
chat_repo = cast(ChatRepository, chat_repository)
poster_request_repo = poster_request_repository
# For backward compatibility with some codes
inline_user_repo = user_repo

from models.phrase import Phrase as Phrase, LongPhrase as LongPhrase  # noqa: E402
from models.proposal import Proposal as Proposal, LongProposal as LongProposal  # noqa: E402

from services.phrase_service import PhraseService  # noqa: E402
from services.proposal_service import ProposalService  # noqa: E402
from services.user_service import UserService  # noqa: E402
from services.ai_service import ai_service  # noqa: E402
from services.tts_service import tts_service  # noqa: E402
from services.cunhao_agent import cunhao_agent  # noqa: E402
from services.usage_service import usage_service  # noqa: E402
from services.badge_service import badge_service  # noqa: E402

# Services initialized with explicit repo protocols
phrase_service = PhraseService(phrase_repo, long_phrase_repo)
user_service = UserService(user_repo, chat_repo)
proposal_service = ProposalService(
    proposal_repo,
    long_proposal_repo,
    user_repo,
)

__all__ = [
    "phrase_repo",
    "long_phrase_repo",
    "proposal_repo",
    "long_proposal_repo",
    "user_repo",
    "inline_user_repo",
    "phrase_service",
    "user_service",
    "proposal_service",
    "ai_service",
    "tts_service",
    "cunhao_agent",
    "usage_service",
    "badge_service",
    "poster_request_repo",
]
