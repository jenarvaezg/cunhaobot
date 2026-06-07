import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING
from telegram import Update
from telegram.error import BadRequest, TelegramError

from models.proposal import Proposal, LongProposal
from infrastructure.protocols import (
    ProposalRepository,
    LongProposalRepository,
    UserRepository,
)
from core.config import config

if TYPE_CHECKING:
    from services.user_service import UserService
    from services.phrase_service import PhraseService

logger = logging.getLogger(__name__)

# A Propuesta whose similarity to existing content is above this threshold is
# treated as a duplicate rather than accepted into the Consejo voting flow.
SIMILARITY_DISCARD_THRESHOLD = 90


class IntakeStatus(Enum):
    """Outcome of submitting a Propuesta for Consejo evaluation."""

    EMPTY = "empty"
    DUPLICATE_APPROVED = "duplicate_approved"
    DUPLICATE_ACTIVE = "duplicate_active"
    DUPLICATE_REJECTED = "duplicate_rejected"
    ACCEPTED = "accepted"


@dataclass(frozen=True)
class IntakeResult:
    """Result of Pieza cuñadil intake, carrying the decision plus any context a
    caller needs to format a platform response (no platform objects involved)."""

    status: IntakeStatus
    proposal: Proposal | None = None
    similar_text: str = ""
    similarity: int = 0


class ProposalService:
    def __init__(
        self,
        repo: ProposalRepository,
        long_repo: LongProposalRepository,
        user_repo: UserRepository,
        user_service: UserService,
        phrase_service: PhraseService,
    ):
        self.repo = repo
        self.long_repo = long_repo
        self.user_repo = user_repo
        self.user_service = user_service
        self.phrase_service = phrase_service
        self._curators_cache: dict[str, str] = {}
        self._last_update: datetime | None = None

    async def submit(self, proposal: Proposal) -> IntakeResult:
        """Run Pieza cuñadil intake for a Propuesta and decide its fate.

        Owns the whole decision: empty text, duplicate against approved Pieza
        cuñadil, duplicate against an active Propuesta, duplicate against a
        rejected Propuesta, or acceptance into the Consejo voting flow. The
        Apelativo vs Frase cuñadil split is derived from the proposal type so
        callers never pick a repository.
        """
        is_long = isinstance(proposal, LongProposal)

        if not proposal.text:
            return IntakeResult(IntakeStatus.EMPTY)

        (
            most_similar_phrase,
            phrase_similarity,
        ) = await self.phrase_service.find_most_similar(proposal.text, long=is_long)
        if phrase_similarity > SIMILARITY_DISCARD_THRESHOLD:
            return IntakeResult(
                IntakeStatus.DUPLICATE_APPROVED,
                similar_text=most_similar_phrase.text,
                similarity=phrase_similarity,
            )

        (
            most_similar_proposal,
            proposal_similarity,
        ) = await self.find_most_similar_proposal(proposal.text, is_long=is_long)
        if (
            proposal_similarity > SIMILARITY_DISCARD_THRESHOLD
            and most_similar_proposal is not None
        ):
            status = (
                IntakeStatus.DUPLICATE_REJECTED
                if most_similar_proposal.voting_ended
                else IntakeStatus.DUPLICATE_ACTIVE
            )
            return IntakeResult(
                status,
                proposal=most_similar_proposal,
                similar_text=most_similar_proposal.text,
                similarity=proposal_similarity,
            )

        if isinstance(proposal, LongProposal):
            await self.long_repo.save(proposal)
        else:
            await self.repo.save(proposal)

        return IntakeResult(
            IntakeStatus.ACCEPTED,
            proposal=proposal,
            similar_text=most_similar_phrase.text,
            similarity=phrase_similarity,
        )

    def create_from_update(
        self, update: Update, is_long: bool = False, text: str | None = None
    ) -> Proposal:
        if not (msg := update.effective_message) or not (user := update.effective_user):
            raise ValueError("Invalid update")

        proposal_id = str(msg.chat.id + msg.message_id)
        klass = LongProposal if is_long else Proposal

        if text is None:
            raw = msg.text or ""
            if raw.startswith("/"):
                parts = raw.split(" ", 1)
                text = parts[1].strip() if len(parts) > 1 else ""
            else:
                text = raw

            if not text and msg.reply_to_message:
                text = msg.reply_to_message.text or ""

        return klass(
            id=proposal_id,
            from_chat_id=msg.chat.id,
            from_message_id=msg.message_id,
            text=text.strip() if text else "",
            user_id=user.id,
        )

    async def vote(
        self, proposal: Proposal, voter_id: str | int, positive: bool
    ) -> None:
        voter_id_str = str(voter_id)
        liked = set(proposal.liked_by)
        disliked = set(proposal.disliked_by)

        if positive:
            disliked.discard(voter_id_str)
            liked.add(voter_id_str)
        else:
            liked.discard(voter_id_str)
            disliked.add(voter_id_str)

        proposal.liked_by, proposal.disliked_by = list(liked), list(disliked)
        if isinstance(proposal, LongProposal):
            await self.long_repo.save(proposal)
        else:
            await self.repo.save(proposal)

        # Award points: 1 to proposer
        await self.user_service.add_points(proposal.user_id, 1)

    async def get_curators(self) -> dict[str, str]:
        now = datetime.now()
        if not self._last_update or (now - self._last_update) > timedelta(minutes=10):
            await self._update_curators_cache()
        return self._curators_cache

    async def _update_curators_cache(self):
        from tg import get_initialized_tg_application

        try:
            application = await get_initialized_tg_application()
            bot = application.bot
            new_cache: dict[str, str] = {}
            admins = await bot.get_chat_administrators(chat_id=config.mod_chat_id)
            for admin in admins:
                if not admin.user.is_bot:
                    new_cache[str(admin.user.id)] = (
                        admin.user.name or admin.user.first_name
                    )

            all_proposals = await self.repo.load_all() + await self.long_repo.load_all()
            active_ids = {str(p.user_id) for p in all_proposals}
            for p in all_proposals:
                active_ids.update(str(uid) for uid in p.liked_by)
                active_ids.update(str(uid) for uid in p.disliked_by)

            ids_to_check = active_ids - set(new_cache.keys()) - {"0"}

            async def check_user(uid):
                try:
                    # Telegram API requires int for numeric IDs
                    target_id = int(uid) if uid.lstrip("-").isdigit() else uid
                    m = await bot.get_chat_member(
                        chat_id=config.mod_chat_id, user_id=target_id
                    )
                    if m.status in ["member", "administrator", "creator"]:
                        return uid
                except (BadRequest, TelegramError, ValueError):
                    pass
                return None

            check_tasks = [check_user(uid) for uid in list(ids_to_check)[:100]]
            member_ids = await asyncio.gather(*check_tasks)

            # Unify db names lookup
            db_names: dict[str, str] = {
                str(u.id): u.name
                for u in await self.user_repo.load_all(ignore_gdpr=True)
            }

            for mid in member_ids:
                if mid and mid not in new_cache:
                    new_cache[str(mid)] = db_names.get(str(mid), f"User {mid}")

            self._curators_cache = new_cache
            self._last_update = datetime.now()
        except Exception as e:
            logger.error(f"Error updating curators: {e}")

    async def approve(self, proposal_kind: str, proposal_id: str) -> bool:
        repo = self.long_repo if proposal_kind == LongProposal.kind else self.repo
        proposal = await repo.load(proposal_id)
        if not proposal:
            return False
        from tg.handlers.utils.callback_query import approve_proposal
        from tg import get_initialized_tg_application

        app = await get_initialized_tg_application()
        await approve_proposal(proposal, app.bot)
        return True

    async def reject(self, proposal_kind: str, proposal_id: str) -> bool:
        repo = self.long_repo if proposal_kind == LongProposal.kind else self.repo
        proposal = await repo.load(proposal_id)
        if not proposal:
            return False
        from tg.handlers.utils.callback_query import dismiss_proposal
        from tg import get_initialized_tg_application

        app = await get_initialized_tg_application()
        await dismiss_proposal(proposal, app.bot)
        return True

    async def find_most_similar_proposal(
        self, text: str, is_long: bool = False
    ) -> tuple[Proposal | None, int]:
        from fuzzywuzzy import fuzz
        from utils import normalize_str

        repo = self.long_repo if is_long else self.repo
        proposals = await repo.load_all()
        if not proposals:
            return None, 0

        norm_text = normalize_str(text)

        # Calculate similarity for all proposals
        # We handle Proposal and LongProposal which have 'text' attribute
        scored_proposals = [
            (p, fuzz.ratio(norm_text, normalize_str(p.text))) for p in proposals
        ]

        if not scored_proposals:
            return None, 0

        return max(scored_proposals, key=lambda x: x[1])
