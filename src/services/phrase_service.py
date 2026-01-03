from io import BytesIO
import logging
import random
from datetime import datetime
from typing import TYPE_CHECKING, cast

import telegram
from fuzzywuzzy import fuzz
from models.phrase import Phrase, LongPhrase
from infrastructure.protocols import PhraseRepository, LongPhraseRepository
from utils import normalize_str

if TYPE_CHECKING:
    from models.proposal import Proposal, LongProposal

logger = logging.getLogger(__name__)


class PhraseService:
    def __init__(
        self, phrase_repo: PhraseRepository, long_phrase_repo: LongPhraseRepository
    ):
        self.phrase_repo = phrase_repo
        self.long_repo = long_phrase_repo

    def create_sticker_image(self, phrase: Phrase | LongPhrase) -> bytes:
        from utils.image_utils import generate_png

        is_long = isinstance(phrase, LongPhrase)
        text = phrase.text if is_long else f"¿Qué pasa, {phrase.text}?"
        return generate_png(text).getvalue()

    async def create_from_proposal(
        self, proposal: "Proposal | LongProposal", bot: telegram.Bot
    ) -> None:
        from models.proposal import LongProposal
        from tg.stickers import upload_sticker
        from services.user_service import user_service

        is_long = isinstance(proposal, LongProposal)
        model_class = LongPhrase if is_long else Phrase

        phrase = model_class(
            text=proposal.text,
            user_id=proposal.user_id,
            chat_id=proposal.from_chat_id,
            created_at=datetime.now(),
            proposal_id=proposal.id,
            score=(len(proposal.liked_by) - len(proposal.disliked_by)) * 5,
        )

        sticker_image = self.create_sticker_image(phrase)
        phrase.sticker_file_id = await upload_sticker(
            bot,
            BytesIO(sticker_image),
            phrase.stickerset_template,
            phrase.stickerset_title_template,
        )
        if is_long:
            await self.long_repo.save(cast(LongPhrase, phrase))
        else:
            await self.phrase_repo.save(phrase)

        # Award points to the proposer
        user_service.add_points(proposal.user_id, 10)

        # Check for badges (Poeta) and notify
        from services.badge_service import badge_service
        from utils.ui import format_badge_notification

        new_badges = await badge_service.check_badges(proposal.user_id, "telegram")
        for badge in new_badges:
            try:
                await bot.send_message(
                    chat_id=proposal.user_id,
                    text=await format_badge_notification(badge),
                    parse_mode=telegram.constants.ParseMode.HTML,
                )
            except Exception as e:
                logger.warning(
                    f"Could not notify badge {badge.id} to user {proposal.user_id}: {e}"
                )

    async def get_random(self, long: bool = False) -> Phrase:
        repo = self.long_repo if long else self.phrase_repo
        phrases = await repo.load_all()
        if not phrases:
            return LongPhrase(text="¡Cuñado!") if long else Phrase(text="¡Cuñado!")
        return random.choice(phrases)

    async def get_phrases(
        self, search: str, long: bool = False
    ) -> list[Phrase | LongPhrase]:
        repo = self.long_repo if long else self.phrase_repo
        phrases = await repo.load_all()
        return [p for p in phrases if search.lower() in p.text.lower()]

    async def find_most_similar(
        self, text: str, long: bool = False
    ) -> tuple[Phrase, int]:
        repo = self.long_repo if long else self.phrase_repo
        phrases = await repo.load_all()
        if not phrases:
            return (LongPhrase(text="") if long else Phrase(text="")), 0

        norm_text = normalize_str(text)
        return max(
            [(p, fuzz.ratio(norm_text, normalize_str(p.text))) for p in phrases],
            key=lambda x: x[1],
        )

    async def register_sticker_usage(self, phrase: Phrase | LongPhrase) -> None:
        """Increments sticker usage counters for a phrase."""
        phrase.usages += 1
        phrase.sticker_usages += 1
        phrase.score += 1

        if isinstance(phrase, LongPhrase):
            await self.long_repo.save(phrase)
        else:
            await self.phrase_repo.save(phrase)

    async def add_usage_by_id(self, result_id: str) -> None:
        """Increments usage count based on inline result ID."""
        is_audio = result_id.startswith("audio-")
        is_sticker = result_id.startswith("sticker-")

        # Remove prefix
        clean_id = result_id
        if is_audio:
            clean_id = result_id.replace("audio-", "", 1)
        if is_sticker:
            clean_id = result_id.replace("sticker-", "", 1)

        is_long = clean_id.startswith("long-")
        is_short = clean_id.startswith("short-")

        if not is_long and not is_short:
            return

        # In short mode it can be multiple words separated by comma
        data = (
            clean_id.replace("long-", "", 1)
            if is_long
            else clean_id.replace("short-", "", 1)
        )
        items = data.split(",") if is_short else [data]

        for item in items:
            # Numeric ID only
            if item.isdigit():
                phrase_id = int(item)
                if is_long:
                    lp = await self.long_repo.load(phrase_id)
                    if lp:
                        lp.usages += 1
                        lp.score += 1
                        if is_audio:
                            lp.audio_usages += 1
                        if is_sticker:
                            lp.sticker_usages += 1
                        await self.long_repo.save(lp)
                else:
                    p = await self.phrase_repo.load(phrase_id)
                    if p:
                        p.usages += 1
                        p.score += 1
                        if is_audio:
                            p.audio_usages += 1
                        if is_sticker:
                            p.sticker_usages += 1
                        await self.phrase_repo.save(p)
