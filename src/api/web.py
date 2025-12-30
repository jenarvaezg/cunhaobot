import logging
from typing import Any, Annotated, cast
from litestar import Controller, Request, get, post
from litestar.exceptions import HTTPException
from litestar.response import Response, Template
from litestar.plugins.htmx import HTMXTemplate, HTMXRequest
from litestar.params import Dependency

from infrastructure.protocols import (
    PhraseRepository,
    LongPhraseRepository,
    ProposalRepository,
    LongProposalRepository,
    UserRepository,
    InlineUserRepository,
)
from services import PhraseService, UserService
from services.ai_service import AIService
from core.config import config

logger = logging.getLogger(__name__)


class WebController(Controller):
    @get("/", sync_to_thread=True)
    def index(
        self,
        request: HTMXRequest,
        phrase_repo: Annotated[Any, Dependency()],
        long_phrase_repo: Annotated[Any, Dependency()],
    ) -> Template:
        # Cast to protocol for internal type safety
        p_repo: PhraseRepository = phrase_repo
        lp_repo: LongPhraseRepository = long_phrase_repo

        short_phrases = p_repo.get_phrases(limit=50)
        long_phrases = lp_repo.get_phrases(limit=50)

        return Template(
            template_name="index.html",
            context={
                "short_phrases": sorted(
                    short_phrases, key=lambda x: x.usages, reverse=True
                ),
                "long_phrases": sorted(
                    long_phrases, key=lambda x: x.usages, reverse=True
                ),
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "is_htmx": bool(request.htmx),
            },
        )

    @get("/phrase/{phrase_id:str}")
    async def phrase_detail(
        self,
        request: Request,
        phrase_id: str,
        phrase_repo: Annotated[Any, Dependency()],
        long_phrase_repo: Annotated[Any, Dependency()],
        inline_user_repo: Annotated[Any, Dependency()],
        user_repo: Annotated[Any, Dependency()],
    ) -> Template:
        p_repo: PhraseRepository = phrase_repo
        lp_repo: LongPhraseRepository = long_phrase_repo
        iu_repo: InlineUserRepository = inline_user_repo
        u_repo: UserRepository = user_repo

        phrase = p_repo.load(phrase_id) or lp_repo.load(phrase_id)

        if not phrase:
            raise HTTPException(status_code=404, detail="Phrase not found")

        contributor = None
        if phrase.user_id:
            contributor = iu_repo.load(phrase.user_id) or u_repo.load(phrase.user_id)

            # If not in DB, try to fetch from Telegram
            if not contributor:
                from tg import get_tg_application
                from models.user import InlineUser

                try:
                    application = get_tg_application()
                    if not application.running:
                        await application.initialize()
                    chat = await application.bot.get_chat(phrase.user_id)
                    contributor = InlineUser(
                        user_id=chat.id,
                        name=chat.full_name or chat.first_name or f"User {chat.id}",
                        username=chat.username,
                    )
                    # Save for next time
                    iu_repo.save(contributor)
                except Exception as e:
                    logger.warning(
                        f"Could not fetch user info from Telegram for {phrase.user_id}: {e}"
                    )

        return Template(
            template_name="phrase_detail.html",
            context={
                "phrase": phrase,
                "contributor": contributor,
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
            },
        )

    @get("/user/{user_id:int}/photo.png")
    async def user_photo(
        self,
        user_id: int,
        user_service: Annotated[UserService, Dependency()],
    ) -> Response:
        photo_bytes = await user_service.get_user_photo(user_id)
        if not photo_bytes:
            raise HTTPException(status_code=404, detail="Photo not found")

        return Response(
            content=photo_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    @get("/phrase/{phrase_id:str}/sticker.png", sync_to_thread=True)
    def phrase_sticker(
        self,
        phrase_id: str,
        phrase_repo: Annotated[Any, Dependency()],
        long_phrase_repo: Annotated[Any, Dependency()],
        phrase_service: Annotated[PhraseService, Dependency()],
    ) -> Response:
        p_repo: PhraseRepository = phrase_repo
        lp_repo: LongPhraseRepository = long_phrase_repo

        phrase = p_repo.load(phrase_id) or lp_repo.load(phrase_id)

        if not phrase:
            raise HTTPException(status_code=404, detail="Phrase not found")

        sticker_bytes = phrase_service.create_sticker_image(phrase)
        return Response(
            content=sticker_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=31536000"},
        )

    @get("/proposals", sync_to_thread=True)
    def proposals(
        self,
        request: HTMXRequest,
        proposal_repo: Annotated[Any, Dependency()],
        long_proposal_repo: Annotated[Any, Dependency()],
    ) -> Template:
        from .utils import get_proposals_context

        return Template(
            template_name="proposals.html",
            context=cast(
                dict[str, Any],
                get_proposals_context(request, proposal_repo, long_proposal_repo),
            ),
        )

    @get("/search", sync_to_thread=True)
    def search(
        self,
        request: HTMXRequest,
        phrase_repo: Annotated[Any, Dependency()],
        long_phrase_repo: Annotated[Any, Dependency()],
        search: str = "",
        **filters: Any,
    ) -> HTMXTemplate:
        p_repo: PhraseRepository = phrase_repo
        lp_repo: LongPhraseRepository = long_phrase_repo

        short_phrases = p_repo.get_phrases(search=search, **filters)
        long_phrases = lp_repo.get_phrases(search=search, **filters)
        return HTMXTemplate(
            template_name="partials/phrases_list.html",
            context={
                "short_phrases": sorted(
                    short_phrases, key=lambda x: x.usages, reverse=True
                ),
                "long_phrases": sorted(
                    long_phrases, key=lambda x: x.usages, reverse=True
                ),
                "is_htmx": bool(request.htmx),
            },
        )

    @post("/ai/generate")
    async def generate_ai_phrases(
        self, request: Request, ai_service: Annotated[Any, Dependency()]
    ) -> Response[dict[str, Any]]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != str(config.owner_id):
            return Response({"error": "Unauthorized"}, status_code=401)

        try:
            # Type safety via casting
            service: AIService = ai_service
            phrases = await service.generate_cunhao_phrases(count=5)
            return Response({"phrases": phrases}, status_code=200)
        except Exception as e:
            return Response({"error": str(e)}, status_code=500)

    @get("/metrics", sync_to_thread=True)
    def metrics(
        self,
        request: Request,
        phrase_repo: Annotated[Any, Dependency()],
        long_phrase_repo: Annotated[Any, Dependency()],
        proposal_repo: Annotated[Any, Dependency()],
        long_proposal_repo: Annotated[Any, Dependency()],
        user_repo: Annotated[Any, Dependency()],
        inline_user_repo: Annotated[Any, Dependency()],
    ) -> Template:
        from collections import defaultdict
        import json

        p_repo: PhraseRepository = phrase_repo
        lp_repo: LongPhraseRepository = long_phrase_repo
        prop_repo: ProposalRepository = proposal_repo
        l_prop_repo: LongProposalRepository = long_proposal_repo

        # Top phrases
        phrases = p_repo.get_phrases() + lp_repo.get_phrases()
        top_phrases = sorted(
            phrases,
            key=lambda p: p.usages + p.audio_usages,
            reverse=True,
        )[:10]

        # Proposal stats
        proposals = prop_repo.load_all() + l_prop_repo.load_all()
        pending_proposals = [p for p in proposals if not p.voting_ended]
        ended_proposals = [p for p in proposals if p.voting_ended]

        # This is a simplification. A proposal is approved if a phrase is created from it.
        # For this metric, we'll assume likes > dislikes means approved.
        approved_proposals = [
            p for p in ended_proposals if len(p.liked_by) > len(p.disliked_by)
        ]
        rejected_proposals = [
            p for p in ended_proposals if len(p.liked_by) <= len(p.disliked_by)
        ]

        proposal_stats = {
            "pending": len(pending_proposals),
            "approved": len(approved_proposals),
            "rejected": len(rejected_proposals),
        }

        # User stats
        user_map: dict[int, str] = {}
        for u in inline_user_repo.load_all():
            user_map[u.user_id] = u.name
        for u in user_repo.load_all(ignore_gdpr=True):
            if not u.is_group:
                user_map[u.chat_id] = u.name

        stats: dict[int, dict[str, Any]] = defaultdict(
            lambda: {"approved": 0, "pending": 0, "score": 0, "name": "Anónimo"}
        )

        for p in phrases:
            s = stats[p.user_id]
            s["approved"] += 1
            s["score"] += 10 + p.usages + p.audio_usages
            if p.user_id in user_map:
                s["name"] = user_map[p.user_id]

        for p in pending_proposals:
            if p.user_id == 0:
                continue
            s = stats[p.user_id]
            s["pending"] += 1
            if p.user_id in user_map:
                s["name"] = user_map[p.user_id]

        sorted_stats = sorted(
            stats.values(), key=lambda x: (x["score"], x["approved"]), reverse=True
        )
        top_contributor = sorted_stats[0]["name"] if sorted_stats else "Nadie"

        # Chart data
        top_5_phrases_chart = {
            "labels": [p.text for p in top_phrases[:5]],
            "data": [p.usages + p.audio_usages for p in top_phrases[:5]],
        }

        return Template(
            template_name="metrics.html",
            context={
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "total_phrases": len(phrases),
                "proposal_stats": proposal_stats,
                "top_contributor": top_contributor,
                "user_stats": sorted_stats,
                "top_phrases": top_phrases,
                "proposal_stats_json": json.dumps(proposal_stats),
                "top_5_phrases_chart_json": json.dumps(top_5_phrases_chart),
            },
        )
