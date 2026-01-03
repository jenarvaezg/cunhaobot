from litestar.di import Provide
from infrastructure.datastore.phrase import phrase_repository, long_phrase_repository
from infrastructure.datastore.proposal import (
    proposal_repository,
    long_proposal_repository,
)
from infrastructure.datastore.user import user_repository
from infrastructure.datastore.chat import chat_repository
from infrastructure.datastore.usage import usage_repository
from infrastructure.datastore.poster_request import poster_request_repository

from services.phrase_service import PhraseService
from services.proposal_service import ProposalService
from services.user_service import UserService
from services.ai_service import ai_service
from services.tts_service import tts_service
from services.badge_service import badge_service
from services.usage_service import usage_service

from infrastructure.protocols import (
    PhraseRepository,
    LongPhraseRepository,
    ProposalRepository,
    LongProposalRepository,
    UserRepository,
    ChatRepository,
)


def provide_phrase_service(
    phrase_repo: PhraseRepository,
    long_phrase_repo: LongPhraseRepository,
) -> PhraseService:
    return PhraseService(phrase_repo, long_phrase_repo)


def provide_user_service(
    user_repo: UserRepository,
    chat_repo: ChatRepository,
) -> UserService:
    return UserService(user_repo, chat_repo)


def provide_proposal_service(
    proposal_repo: ProposalRepository,
    long_proposal_repo: LongProposalRepository,
    user_repo: UserRepository,
) -> ProposalService:
    return ProposalService(proposal_repo, long_proposal_repo, user_repo)


dependencies = {
    "phrase_repo": Provide(lambda: phrase_repository, sync_to_thread=False),
    "long_phrase_repo": Provide(lambda: long_phrase_repository, sync_to_thread=False),
    "proposal_repo": Provide(lambda: proposal_repository, sync_to_thread=False),
    "long_proposal_repo": Provide(
        lambda: long_proposal_repository, sync_to_thread=False
    ),
    "user_repo": Provide(lambda: user_repository, sync_to_thread=False),
    "chat_repo": Provide(lambda: chat_repository, sync_to_thread=False),
    "usage_repo": Provide(lambda: usage_repository, sync_to_thread=False),
    "poster_request_repo": Provide(
        lambda: poster_request_repository, sync_to_thread=False
    ),
    "phrase_service": Provide(provide_phrase_service, sync_to_thread=False),
    "user_service": Provide(provide_user_service, sync_to_thread=False),
    "proposal_service": Provide(provide_proposal_service, sync_to_thread=False),
    "ai_service": Provide(lambda: ai_service, sync_to_thread=False),
    "tts_service": Provide(lambda: tts_service, sync_to_thread=False),
    "badge_service": Provide(lambda: badge_service, sync_to_thread=False),
    "usage_service": Provide(lambda: usage_service, sync_to_thread=False),
}
