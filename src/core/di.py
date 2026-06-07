"""Litestar dependency wiring.

The `Container` in ``core.container`` is the single composition root for the
whole app (Litestar, Telegram and CLI). Here we only expose its singletons to
Litestar's DI by name, so wiring lives in one place and cannot drift between
the web app and the bot.
"""

from litestar.di import Provide

from core.container import services

dependencies = {
    # Repositories
    "phrase_repo": Provide(lambda: services.phrase_repo, sync_to_thread=False),
    "long_phrase_repo": Provide(
        lambda: services.long_phrase_repo, sync_to_thread=False
    ),
    "proposal_repo": Provide(lambda: services.proposal_repo, sync_to_thread=False),
    "long_proposal_repo": Provide(
        lambda: services.long_proposal_repo, sync_to_thread=False
    ),
    "user_repo": Provide(lambda: services.user_repo, sync_to_thread=False),
    "chat_repo": Provide(lambda: services.chat_repo, sync_to_thread=False),
    "usage_repo": Provide(lambda: services.usage_repo, sync_to_thread=False),
    "link_request_repo": Provide(
        lambda: services.link_request_repo, sync_to_thread=False
    ),
    "poster_request_repo": Provide(
        lambda: services.poster_request_repo, sync_to_thread=False
    ),
    "gift_repo": Provide(lambda: services.gift_repo, sync_to_thread=False),
    # Services
    "badge_service": Provide(lambda: services.badge_service, sync_to_thread=False),
    "user_service": Provide(lambda: services.user_service, sync_to_thread=False),
    "phrase_service": Provide(lambda: services.phrase_service, sync_to_thread=False),
    "proposal_service": Provide(
        lambda: services.proposal_service, sync_to_thread=False
    ),
    "usage_service": Provide(lambda: services.usage_service, sync_to_thread=False),
    "ai_service": Provide(lambda: services.ai_service, sync_to_thread=False),
    "tts_service": Provide(lambda: services.tts_service, sync_to_thread=False),
    "game_service": Provide(lambda: services.game_service, sync_to_thread=False),
    "profile_service": Provide(lambda: services.profile_service, sync_to_thread=False),
    "cunhao_agent": Provide(lambda: services.cunhao_agent, sync_to_thread=False),
    "chat_interaction_service": Provide(
        lambda: services.chat_interaction_service, sync_to_thread=False
    ),
}
