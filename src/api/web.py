import logging
import asyncio
from typing import Any, Annotated
from litestar import Controller, Request, get, post
from litestar.exceptions import HTTPException
from litestar.response import Response, Template
from litestar.plugins.htmx import HTMXTemplate
from litestar.params import Dependency

from infrastructure.protocols import (
    PhraseRepository,
    LongPhraseRepository,
    ProposalRepository,
    LongProposalRepository,
    UserRepository,
    GiftRepository,
)
from services import PhraseService, UserService, tts_service as tts_service_instance
from services.ai_service import AIService
from core.config import config

logger = logging.getLogger(__name__)


class WebController(Controller):
    @get("/")
    async def index(
        self,
        request: Request,
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
    ) -> Template:
        short_phrases = await phrase_repo.load_all()
        long_phrases = await long_phrase_repo.load_all()

        return Template(
            template_name="index.html",
            context={
                "short_phrases": sorted(
                    short_phrases, key=lambda x: x.usages, reverse=True
                )[:50],
                "long_phrases": sorted(
                    long_phrases, key=lambda x: x.usages, reverse=True
                )[:50],
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "is_htmx": bool(getattr(request, "htmx", False)),
                "request": request,
            },
        )

    @get("/phrase/{phrase_id:int}")
    async def phrase_detail(
        self,
        request: Request,
        phrase_id: int,
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
        user_repo: Annotated[UserRepository, Dependency()],
    ) -> Template:
        phrase = await phrase_repo.load(phrase_id) or await long_phrase_repo.load(
            phrase_id
        )

        if not phrase:
            raise HTTPException(status_code=404, detail="Phrase not found")

        contributor = None
        if phrase.user_id:
            contributor = await user_repo.load(phrase.user_id)

            # If not in DB, try to fetch from Telegram
            if not contributor:
                from tg import get_tg_application
                from models.user import User

                try:
                    application = get_tg_application()
                    if not application.running:
                        await application.initialize()
                    chat = await application.bot.get_chat(phrase.user_id)
                    contributor = User(
                        id=chat.id,
                        name=chat.full_name or chat.first_name or f"User {chat.id}",
                        username=chat.username,
                    )
                    # Save for next time
                    await user_repo.save(contributor)
                except Exception as e:
                    logger.warning(
                        f"Could not fetch user info from Telegram for {phrase.user_id}: {e}"
                    )

        # Check if AI image exists in GCS
        from utils.gcp import get_bucket

        image_url = None
        try:
            bucket = get_bucket()
            blob = bucket.blob(f"generated_images/{phrase_id}.png")
            if blob.exists():
                image_url = blob.public_url
        except Exception as e:
            logger.warning(f"Could not check for AI image existence: {e}")

        return Template(
            template_name="phrase_detail.html",
            context={
                "phrase": phrase,
                "contributor": contributor,
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "image_url": image_url,
                "request": request,
            },
        )

    @get("/user/{user_id:str}/photo.png")
    async def user_photo(
        self,
        user_id: str,
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

    @get("/user/{user_id:str}/profile")
    async def profile(
        self,
        request: Request,
        user_id: str,
        user_repo: Annotated[UserRepository, Dependency()],
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
        gift_repo: Annotated[GiftRepository, Dependency()],
    ) -> Template | Response:
        from services.badge_service import badge_service
        from services.usage_service import usage_service
        from services import poster_request_repo
        from models.gift import GIFT_EMOJIS, GIFT_NAMES

        # Try to find user (load will follow links)
        profile_user = await user_repo.load(user_id)
        if not profile_user:
            # Try numeric ID if string failed (legacy compatibility)
            try:
                profile_user = await user_repo.load(int(user_id))
            except ValueError:
                pass

        if not profile_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # If the requested ID is an alias (linked_to), redirect to the master profile
        if str(profile_user.id) != str(user_id):
            return Response(
                status_code=307,
                content=b"",
                headers={"Location": f"/user/{profile_user.id}/profile"},
            )

        # Parallelize data fetching
        stats_task = usage_service.get_user_stats(profile_user.id)
        badges_task = badge_service.get_all_badges_progress(
            profile_user.id, profile_user.platform, user=profile_user
        )
        phrases_task = phrase_repo.get_phrases(user_id=str(profile_user.id))
        long_phrases_task = long_phrase_repo.get_phrases(user_id=str(profile_user.id))
        posters_task = poster_request_repo.get_completed_by_user(profile_user.id)

        try:
            gifts_task = gift_repo.get_gifts_for_user(int(profile_user.id))
        except ValueError:
            # Handle non-numeric IDs (e.g. Slack)
            async def _empty_gifts():
                return []

            gifts_task = _empty_gifts()

        (
            stats,
            badges_progress,
            user_phrases,
            user_long_phrases,
            user_posters,
            user_gifts,
        ) = await asyncio.gather(
            stats_task,
            badges_task,
            phrases_task,
            long_phrases_task,
            posters_task,
            gifts_task,
        )

        all_user_phrases = sorted(
            user_phrases + user_long_phrases, key=lambda x: x.usages, reverse=True
        )

        # Calculate Level (simple formula)
        level = 1 + int(profile_user.points / 100)

        # Mock fun stats for now (could be improved with more complex queries)
        fun_stats = {}
        if stats["total_usages"] > 0:
            # If we had detailed usage logs we could do more here
            pass

        return Template(
            template_name="profile.html",
            context={
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "profile_user": profile_user,
                "stats": stats,
                "badges_progress": badges_progress,
                "user_phrases": all_user_phrases,
                "user_posters": user_posters,
                "user_gifts": user_gifts,
                "gift_emojis": GIFT_EMOJIS,
                "gift_names": GIFT_NAMES,
                "phrases_count": len(all_user_phrases),
                "level": level,
                "fun_stats": fun_stats,
                "request": request,
            },
        )

    @post("/profile/toggle-privacy")
    async def toggle_privacy(
        self,
        request: Request,
        user_service: Annotated[UserService, Dependency()],
    ) -> HTMXTemplate | Response:
        user_session = request.session.get("user")
        if not user_session:
            return Response({"error": "Unauthorized"}, status_code=401)

        user_id = user_session.get("id")
        platform = user_session.get("platform", "telegram")

        is_private = user_service.toggle_privacy(user_id, platform)
        if is_private is None:
            return Response({"error": "User not found"}, status_code=404)

        return HTMXTemplate(
            template_name="partials/privacy_toggle_button.html",
            context={"is_private": is_private},
        )

    @get("/phrase/{phrase_id:int}/audio.ogg")
    async def phrase_audio(
        self,
        request: Request,
        phrase_id: int,
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
    ) -> Response:
        phrase = await phrase_repo.load(phrase_id) or await long_phrase_repo.load(
            phrase_id
        )
        if not phrase:
            raise HTTPException(status_code=404, detail="Phrase not found")

        # Log usage if user is logged in
        user_session = request.session.get("user")
        if user_session:
            from services.usage_service import usage_service
            from models.usage import ActionType

            await usage_service.log_usage(
                user_id=user_session.get("id"),
                platform=user_session.get("platform", "telegram"),
                action=ActionType.AUDIO,
                phrase_id=phrase_id,
            )

        result_type = "long" if phrase.kind == "LongPhrase" else "short"
        audio_url = tts_service_instance.get_audio_url(phrase, result_type)

        if not audio_url:
            raise HTTPException(status_code=500, detail="Could not generate audio")

        return Response(
            content=b"",
            status_code=307,
            headers={"Location": audio_url},
        )

    @get("/phrase/{phrase_id:int}/sticker.png")
    async def phrase_sticker(
        self,
        phrase_id: int,
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
        phrase_service: Annotated[PhraseService, Dependency()],
    ) -> Response:
        phrase = await phrase_repo.load(phrase_id) or await long_phrase_repo.load(
            phrase_id
        )

        if not phrase:
            raise HTTPException(status_code=404, detail="Phrase not found")

        sticker_bytes = phrase_service.create_sticker_image(phrase)
        return Response(
            content=sticker_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=31536000"},
        )

    @get("/sticker/text.png", sync_to_thread=True)
    def text_sticker(
        self,
        text: str,
        phrase_service: Annotated[PhraseService, Dependency()],
    ) -> Response:
        from models.phrase import LongPhrase

        phrase = LongPhrase(text=text)
        sticker_bytes = phrase_service.create_sticker_image(phrase)
        return Response(
            content=sticker_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    @get("/proposals")
    async def proposals(
        self,
        request: Request,
        proposal_repo: Annotated[ProposalRepository, Dependency()],
        long_proposal_repo: Annotated[LongProposalRepository, Dependency()],
    ) -> Template:
        from .utils import get_proposals_context

        return Template(
            template_name="proposals.html",
            context=await get_proposals_context(
                request, proposal_repo, long_proposal_repo
            ),
        )

    @get("/ranking")
    async def ranking(
        self,
        request: Request,
        user_repo: Annotated[UserRepository, Dependency()],
    ) -> Template:
        from services.badge_service import BADGES

        # Get all users with points > 0.
        # After refactor, User kind only contains people.
        ranking = [u for u in await user_repo.load_all() if u.points > 0]
        ranking.sort(key=lambda x: x.points, reverse=True)

        badges_map = {b.id: b for b in BADGES}

        return Template(
            template_name="ranking.html",
            context={
                "ranking": ranking,
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "badges_map": badges_map,
                "request": request,
            },
        )

    @get("/privacy", sync_to_thread=True)
    def privacy(self, request: Request) -> Template:
        return Template(
            template_name="privacy.html",
            context={
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "request": request,
            },
        )

    @get("/terms", sync_to_thread=True)
    def terms(self, request: Request) -> Template:
        return Template(
            template_name="terms.html",
            context={
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "request": request,
            },
        )

    @get("/data-policy", sync_to_thread=True)
    def data_policy(self, request: Request) -> Template:
        return Template(
            template_name="data_policy.html",
            context={
                "user": request.session.get("user"),
                "owner_id": config.owner_id,
                "request": request,
            },
        )

    @get("/search")
    async def search(
        self,
        request: Request,
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
        search: str = "",
        **filters: Any,
    ) -> HTMXTemplate:
        short_phrases = await phrase_repo.get_phrases(search=search, **filters)
        long_phrases = await long_phrase_repo.get_phrases(search=search, **filters)
        return HTMXTemplate(
            template_name="partials/phrases_list.html",
            context={
                "short_phrases": sorted(
                    short_phrases, key=lambda x: x.usages, reverse=True
                ),
                "long_phrases": sorted(
                    long_phrases, key=lambda x: x.usages, reverse=True
                ),
                "is_htmx": bool(getattr(request, "htmx", False)),
            },
        )

    @post("/ai/generate")
    async def generate_ai_phrases(
        self,
        request: Request,
        ai_service: Annotated[AIService, Dependency()],
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
    ) -> Response[dict[str, Any]]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != str(config.owner_id):
            return Response({"error": "Unauthorized"}, status_code=401)

        try:
            # Fetch all phrases for context
            context_phrases = [p.text for p in await phrase_repo.load_all()] + [
                p.text for p in await long_phrase_repo.load_all()
            ]

            phrases = await ai_service.generate_cunhao_phrases(
                count=5, context_phrases=context_phrases
            )
            return Response({"phrases": phrases}, status_code=200)
        except Exception as e:
            logger.exception("Error generating AI phrases:")
            return Response({"error": str(e)}, status_code=500)

    @get("/ai/phrase")
    async def ai_phrase(
        self,
        ai_service: Annotated[AIService, Dependency()],
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
        request: Request,
    ) -> HTMXTemplate:
        try:
            # Log usage if user is logged in
            user_session = request.session.get("user")
            if user_session:
                from services.usage_service import usage_service
                from models.usage import ActionType

                await usage_service.log_usage(
                    user_id=user_session.get("id"),
                    platform=user_session.get("platform", "telegram"),
                    action=ActionType.AI_ASK,
                )

            # Fetch all phrases for context
            context_phrases = [p.text for p in await phrase_repo.load_all()] + [
                p.text for p in await long_phrase_repo.load_all()
            ]

            phrases = await ai_service.generate_cunhao_phrases(
                count=1, context_phrases=context_phrases
            )
            phrase = (
                phrases[0]
                if phrases
                else "No se me ocurre nada, mákina. Pídeme un carajillo."
            )
            return HTMXTemplate(
                template_name="partials/ai_phrase.html",
                context={"phrase": phrase},
            )
        except Exception as e:
            logger.exception("Error generating single AI phrase:")
            return HTMXTemplate(
                template_name="partials/ai_phrase.html",
                context={"phrase": f"Error: {str(e)}"},
                status_code=500,
            )

    @post("/phrase/{phrase_id:int}/generate-image")
    async def generate_phrase_image(
        self,
        phrase_id: int,
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
        ai_service: Annotated[AIService, Dependency()],
        request: Request,
    ) -> HTMXTemplate:
        user = request.session.get("user")
        if not user or str(user.get("id")) != str(config.owner_id):
            return HTMXTemplate(
                template_name="partials/ai_image.html",
                context={
                    "error": "Unauthorized: AI image generation is for the owner only."
                },
                status_code=401,
            )

        phrase = await phrase_repo.load(phrase_id) or await long_phrase_repo.load(
            phrase_id
        )
        if not phrase:
            raise HTTPException(status_code=404, detail="Phrase not found")

        try:
            image_bytes = await ai_service.generate_image(phrase.text)

            # Upload to GCS
            from utils.gcp import get_bucket

            bucket = get_bucket()
            # Use a deterministic name but allow for some variety if needed,
            # or just overwrite to save space.
            blob = bucket.blob(f"generated_images/{phrase_id}.png")
            blob.upload_from_string(image_bytes, content_type="image/png")
            blob.make_public()
            image_url = blob.public_url

            return HTMXTemplate(
                template_name="partials/ai_image.html",
                context={"image_url": image_url, "phrase": phrase},
            )
        except Exception as e:
            logger.error(f"Failed to generate image for phrase {phrase_id}: {e}")
            return HTMXTemplate(
                template_name="partials/ai_image.html",
                context={"error": str(e), "phrase": phrase},
            )

    @get("/metrics")
    async def metrics(
        self,
        request: Request,
        phrase_repo: Annotated[PhraseRepository, Dependency()],
        long_phrase_repo: Annotated[LongPhraseRepository, Dependency()],
        proposal_repo: Annotated[ProposalRepository, Dependency()],
        long_proposal_repo: Annotated[LongProposalRepository, Dependency()],
        user_repo: Annotated[UserRepository, Dependency()],
    ) -> Template:
        from collections import Counter
        import json
        from services.badge_service import BADGES

        p_repo: PhraseRepository = phrase_repo
        lp_repo: LongPhraseRepository = long_phrase_repo
        prop_repo: ProposalRepository = proposal_repo
        l_prop_repo: LongProposalRepository = long_proposal_repo

        # Top phrases
        phrases = await p_repo.get_phrases() + await lp_repo.get_phrases()
        top_phrases = sorted(
            phrases,
            key=lambda p: p.usages + p.audio_usages,
            reverse=True,
        )[:10]

        # Proposal stats
        proposals = await prop_repo.load_all() + await l_prop_repo.load_all()
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

        # Badge Stats
        all_users = await user_repo.load_all(ignore_gdpr=True)
        badge_counts: Counter = Counter()
        total_badges = 0
        for u in all_users:
            if u.badges:
                badge_counts.update(u.badges)
                total_badges += len(u.badges)

        badge_stats = []
        for badge in BADGES:
            count = badge_counts.get(badge.id, 0)
            badge_stats.append({"badge": badge, "count": count})

        # Sort badges by rarity (least common first) or popularity (most common first)
        # Let's go with popularity for now
        badge_stats.sort(key=lambda x: x["count"], reverse=True)

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
                "badge_stats": badge_stats,
                "total_badges": total_badges,
                "top_phrases": top_phrases,
                "proposal_stats_json": json.dumps(proposal_stats),
                "top_5_phrases_chart_json": json.dumps(top_5_phrases_chart),
                "request": request,
            },
        )
