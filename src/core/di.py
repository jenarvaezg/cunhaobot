from litestar.di import Provide
from core.config import config
from utils.gcp import get_bucket

from infrastructure.datastore.phrase import phrase_repository, long_phrase_repository
from infrastructure.datastore.proposal import (
    proposal_repository,
    long_proposal_repository,
)
from infrastructure.datastore.user import user_repository
from infrastructure.datastore.chat import chat_repository
from infrastructure.datastore.usage import usage_repository
from infrastructure.datastore.poster_request import poster_request_repository
from infrastructure.datastore.gift import gift_repository
from infrastructure.datastore.link_request import link_request_repository

from services import (
    PhraseService,
    ProposalService,
    UserService,
    GameService,
    AIService,
    TTSService,
    BadgeService,
    UsageService,
    CunhaoAgent,
)

from infrastructure.protocols import (
    PhraseRepository,
    LongPhraseRepository,
    ProposalRepository,
    LongProposalRepository,
    UserRepository,
    ChatRepository,
    UsageRepository,
    GiftRepository,
    LinkRequestRepository,
)


def provide_badge_service(
    user_repo: UserRepository,
    usage_repo: UsageRepository,
    phrase_repo: PhraseRepository,
    long_phrase_repo: LongPhraseRepository,
    gift_repo: GiftRepository,
) -> BadgeService:
    return BadgeService(
        user_repo=user_repo,
        usage_repo=usage_repo,
        phrase_repo=phrase_repo,
        long_phrase_repo=long_phrase_repo,
        gift_repo=gift_repo,
    )


def provide_user_service(
    user_repo: UserRepository,
    chat_repo: ChatRepository,
    phrase_repo: PhraseRepository,
    long_phrase_repo: LongPhraseRepository,
    proposal_repo: ProposalRepository,
    long_proposal_repo: LongProposalRepository,
    link_request_repo: LinkRequestRepository,
) -> UserService:
    return UserService(
        user_repo=user_repo,
        chat_repo=chat_repo,
        phrase_repo=phrase_repo,
        long_phrase_repo=long_phrase_repo,
        proposal_repo=proposal_repo,
        long_proposal_repo=long_proposal_repo,
        link_request_repo=link_request_repo,
    )


def provide_phrase_service(
    phrase_repo: PhraseRepository,
    long_phrase_repo: LongPhraseRepository,
    user_service: UserService,
    badge_service: BadgeService,
) -> PhraseService:
    return PhraseService(
        phrase_repo=phrase_repo,
        long_phrase_repo=long_phrase_repo,
        user_service=user_service,
        badge_service=badge_service,
    )


def provide_proposal_service(
    proposal_repo: ProposalRepository,
    long_proposal_repo: LongProposalRepository,
    user_repo: UserRepository,
    user_service: UserService,
) -> ProposalService:
    return ProposalService(
        repo=proposal_repo,
        long_repo=long_proposal_repo,
        user_repo=user_repo,
        user_service=user_service,
    )


def provide_usage_service(
    usage_repo: UsageRepository,
    user_service: UserService,
    badge_service: BadgeService,
) -> UsageService:
    return UsageService(
        repo=usage_repo,
        user_service=user_service,
        badge_service=badge_service,
    )


def provide_ai_service(phrase_service: PhraseService) -> AIService:
    return AIService(
        api_key=config.gemini_api_key or "dummy",
        phrase_service=phrase_service,
    )


def provide_game_service(
    user_repo: UserRepository, badge_service: BadgeService
) -> GameService:
    return GameService(user_repo=user_repo, badge_service=badge_service)


def provide_tts_service() -> TTSService:
    return TTSService(bucket=get_bucket())


def provide_cunhao_agent() -> CunhaoAgent:
    return CunhaoAgent(api_key=config.gemini_api_key or "dummy")


dependencies = {
    # Repositories
    "phrase_repo": Provide(lambda: phrase_repository, sync_to_thread=False),
    "long_phrase_repo": Provide(lambda: long_phrase_repository, sync_to_thread=False),
    "proposal_repo": Provide(lambda: proposal_repository, sync_to_thread=False),
    "long_proposal_repo": Provide(
        lambda: long_proposal_repository, sync_to_thread=False
    ),
    "user_repo": Provide(lambda: user_repository, sync_to_thread=False),
    "chat_repo": Provide(lambda: chat_repository, sync_to_thread=False),
    "usage_repo": Provide(lambda: usage_repository, sync_to_thread=False),
    "link_request_repo": Provide(lambda: link_request_repository, sync_to_thread=False),
    "poster_request_repo": Provide(
        lambda: poster_request_repository, sync_to_thread=False
    ),
    "gift_repo": Provide(lambda: gift_repository, sync_to_thread=False),
    # Services
    "badge_service": Provide(provide_badge_service, sync_to_thread=False),
    "user_service": Provide(provide_user_service, sync_to_thread=False),
    "phrase_service": Provide(provide_phrase_service, sync_to_thread=False),
    "proposal_service": Provide(provide_proposal_service, sync_to_thread=False),
    "usage_service": Provide(provide_usage_service, sync_to_thread=False),
    "ai_service": Provide(provide_ai_service, sync_to_thread=False),
    "tts_service": Provide(provide_tts_service, sync_to_thread=False),
    "game_service": Provide(provide_game_service, sync_to_thread=False),
    "cunhao_agent": Provide(provide_cunhao_agent, sync_to_thread=False),
}
