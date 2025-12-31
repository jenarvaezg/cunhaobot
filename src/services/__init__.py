from infrastructure.datastore.phrase import phrase_repository, long_phrase_repository
from infrastructure.datastore.proposal import (
    proposal_repository,
    long_proposal_repository,
)
from infrastructure.datastore.user import user_repository, inline_user_repository

# Alias
phrase_repo = phrase_repository
long_phrase_repo = long_phrase_repository
proposal_repo = proposal_repository
long_proposal_repo = long_proposal_repository
user_repo = user_repository
inline_user_repo = inline_user_repository

from models.phrase import Phrase as Phrase, LongPhrase as LongPhrase  # noqa: E402
from models.proposal import Proposal as Proposal, LongProposal as LongProposal  # noqa: E402

from services.phrase_service import PhraseService  # noqa: E402
from services.proposal_service import ProposalService  # noqa: E402
from services.user_service import UserService  # noqa: E402
from services.ai_service import ai_service  # noqa: E402
from services.tts_service import tts_service  # noqa: E402

# Services
phrase_service = PhraseService(phrase_repo, long_phrase_repo)  # type: ignore[arg-type]
user_service = UserService(user_repo, inline_user_repo)  # type: ignore[arg-type]
proposal_service = ProposalService(
    proposal_repo,  # type: ignore[invalid-argument-type]
    long_proposal_repo,  # type: ignore[invalid-argument-type]
    user_repo,  # type: ignore[invalid-argument-type]
    inline_user_repo,  # type: ignore[invalid-argument-type]
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
]
