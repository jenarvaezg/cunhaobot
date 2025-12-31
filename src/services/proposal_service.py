import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.error import BadRequest, TelegramError

from models.proposal import Proposal, LongProposal
from infrastructure.protocols import (
    ProposalRepository,
    LongProposalRepository,
    UserRepository,
)
from services.user_service import user_service
from core.config import config

logger = logging.getLogger(__name__)


class ProposalService:
    def __init__(
        self,
        repo: ProposalRepository,
        long_repo: LongProposalRepository,
        user_repo: UserRepository,
    ):
        self.repo = repo
        self.long_repo = long_repo
        self.user_repo = user_repo
        self._curators_cache: dict[str, str] = {}
        self._last_update: datetime | None = None

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

    def vote(self, proposal: Proposal, voter_id: str | int, positive: bool) -> None:
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
        repo = self.long_repo if isinstance(proposal, LongProposal) else self.repo
        repo.save(proposal)  # type: ignore[arg-type]

        # Award points: 1 to proposer
        user_service.add_points(proposal.user_id, 1)

    async def get_curators(self) -> dict[str, str]:
        now = datetime.now()
        if not self._last_update or (now - self._last_update) > timedelta(minutes=10):
            await self._update_curators_cache()
        return self._curators_cache

    async def _update_curators_cache(self):
        from tg import get_tg_application

        try:
            application = get_tg_application()
            await application.initialize()
            bot = application.bot
            new_cache: dict[str, str] = {}
            admins = await bot.get_chat_administrators(chat_id=config.mod_chat_id)
            for admin in admins:
                if not admin.user.is_bot:
                    new_cache[str(admin.user.id)] = (
                        admin.user.name or admin.user.first_name
                    )

            all_proposals = self.repo.load_all() + self.long_repo.load_all()
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
                str(u.id): u.name for u in self.user_repo.load_all(ignore_gdpr=True)
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
        proposal = repo.load(proposal_id)
        if not proposal:
            return False
        from tg.handlers.utils.callback_query import approve_proposal
        from tg import get_tg_application

        app = get_tg_application()
        await app.initialize()
        await approve_proposal(proposal, app.bot)
        return True

    async def reject(self, proposal_kind: str, proposal_id: str) -> bool:
        repo = self.long_repo if proposal_kind == LongProposal.kind else self.repo
        proposal = repo.load(proposal_id)
        if not proposal:
            return False
        from tg.handlers.utils.callback_query import dismiss_proposal
        from tg import get_tg_application

        app = get_tg_application()
        await app.initialize()
        await dismiss_proposal(proposal, app.bot)
        return True
