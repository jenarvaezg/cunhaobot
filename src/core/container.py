from typing import TYPE_CHECKING, cast
from core.config import config
from utils.gcp import get_bucket

# Concrete repositories
from infrastructure.datastore.phrase import phrase_repository, long_phrase_repository
from infrastructure.datastore.proposal import (
    proposal_repository,
    long_proposal_repository,
)
from infrastructure.datastore.user import user_repository
from infrastructure.datastore.chat import chat_repository
from infrastructure.datastore.usage import usage_repository
from infrastructure.datastore.gift import gift_repository
from infrastructure.datastore.link_request import link_request_repository
from infrastructure.datastore.poster_request import poster_request_repository

# Services
from utils.storage import StorageService
from services import (
    BadgeService,
    UserService,
    PhraseService,
    ProposalService,
    UsageService,
    AIService,
    TTSService,
    CunhaoAgent,
    ProfileService,
    GameService,
    ChatInteractionService,
)

if TYPE_CHECKING:
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
        PosterRequestRepository,
    )


class Container:
    """
    A simple thread-safe singleton container for manual dependency resolution.
    Used by parts of the system where Litestar's DI is not available (e.g. Telegram Bot, CLI).
    """

    def __init__(self):
        # Repositories (already singletons in their modules, we just group them)
        self.phrase_repo: PhraseRepository = phrase_repository
        # The long variants reuse PhraseDatastoreRepository/ProposalDatastoreRepository
        # with a runtime model_class; the static type can't express that polymorphism.
        self.long_phrase_repo: LongPhraseRepository = cast(
            "LongPhraseRepository", long_phrase_repository
        )
        self.proposal_repo: ProposalRepository = proposal_repository
        self.long_proposal_repo: LongProposalRepository = cast(
            "LongProposalRepository", long_proposal_repository
        )
        self.user_repo: UserRepository = user_repository
        self.chat_repo: ChatRepository = chat_repository
        self.usage_repo: UsageRepository = usage_repository
        self.gift_repo: GiftRepository = gift_repository
        self.link_request_repo: LinkRequestRepository = link_request_repository
        self.poster_request_repo: PosterRequestRepository = poster_request_repository

        # Services (Lazily initialized singletons)
        self._badge_service: BadgeService | None = None
        self._user_service: UserService | None = None
        self._phrase_service: PhraseService | None = None
        self._proposal_service: ProposalService | None = None
        self._usage_service: UsageService | None = None
        self._ai_service: AIService | None = None
        self._tts_service: TTSService | None = None
        self._cunhao_agent: CunhaoAgent | None = None
        self._storage_service: StorageService | None = None
        self._profile_service: ProfileService | None = None
        self._game_service: GameService | None = None
        self._chat_interaction_service: ChatInteractionService | None = None

    @property
    def badge_service(self) -> BadgeService:
        if not self._badge_service:
            self._badge_service = BadgeService(
                user_repo=self.user_repo,
                usage_repo=self.usage_repo,
                phrase_repo=self.phrase_repo,
                long_phrase_repo=self.long_phrase_repo,
                gift_repo=self.gift_repo,
            )
        return self._badge_service

    @property
    def user_service(self) -> UserService:
        if not self._user_service:
            self._user_service = UserService(
                user_repo=self.user_repo,
                chat_repo=self.chat_repo,
                phrase_repo=self.phrase_repo,
                long_phrase_repo=self.long_phrase_repo,
                proposal_repo=self.proposal_repo,
                long_proposal_repo=self.long_proposal_repo,
                link_request_repo=self.link_request_repo,
            )
        return self._user_service

    @property
    def phrase_service(self) -> PhraseService:
        if not self._phrase_service:
            self._phrase_service = PhraseService(
                phrase_repo=self.phrase_repo,
                long_phrase_repo=self.long_phrase_repo,
                user_service=self.user_service,
                badge_service=self.badge_service,
            )
        return self._phrase_service

    @property
    def proposal_service(self) -> ProposalService:
        if not self._proposal_service:
            self._proposal_service = ProposalService(
                repo=self.proposal_repo,
                long_repo=self.long_proposal_repo,
                user_repo=self.user_repo,
                user_service=self.user_service,
                phrase_service=self.phrase_service,
            )
        return self._proposal_service

    @property
    def usage_service(self) -> UsageService:
        if not self._usage_service:
            self._usage_service = UsageService(
                repo=self.usage_repo,
                user_service=self.user_service,
                badge_service=self.badge_service,
            )
        return self._usage_service

    @property
    def ai_service(self) -> AIService:
        if not self._ai_service:
            self._ai_service = AIService(
                api_key=config.gemini_api_key or "dummy",
                phrase_service=self.phrase_service,
            )
        return self._ai_service

    @property
    def tts_service(self) -> TTSService:
        if not self._tts_service:
            self._tts_service = TTSService(bucket=get_bucket())
        return self._tts_service

    @property
    def cunhao_agent(self) -> CunhaoAgent:
        if not self._cunhao_agent:
            self._cunhao_agent = CunhaoAgent(api_key=config.gemini_api_key or "dummy")
        return self._cunhao_agent

    @property
    def storage_service(self) -> StorageService:
        if not self._storage_service:
            self._storage_service = StorageService(bucket_name=config.bucket_name)
        return self._storage_service

    @property
    def game_service(self) -> GameService:
        if not self._game_service:
            self._game_service = GameService(
                user_repo=self.user_repo,
                badge_service=self.badge_service,
            )
        return self._game_service

    @property
    def chat_interaction_service(self) -> ChatInteractionService:
        if not self._chat_interaction_service:
            self._chat_interaction_service = ChatInteractionService(
                cunhao_agent=self.cunhao_agent,
                ai_service=self.ai_service,
                usage_service=self.usage_service,
            )
        return self._chat_interaction_service

    @property
    def profile_service(self) -> ProfileService:
        if not self._profile_service:
            self._profile_service = ProfileService(
                phrase_repo=self.phrase_repo,
                long_phrase_repo=self.long_phrase_repo,
                gift_repo=self.gift_repo,
                poster_request_repo=self.poster_request_repo,
                badge_service=self.badge_service,
                usage_service=self.usage_service,
            )
        return self._profile_service


# Global container instance
services = Container()
