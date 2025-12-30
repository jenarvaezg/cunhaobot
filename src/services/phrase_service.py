from io import BytesIO
import logging
import random
from datetime import datetime
from typing import TYPE_CHECKING, Any

import telegram
from fuzzywuzzy import fuzz
from models.phrase import Phrase, LongPhrase
from infrastructure.protocols import PhraseRepository, LongPhraseRepository
from utils import normalize_str

if TYPE_CHECKING:
    pass

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

    async def create_from_proposal(self, proposal: Any, bot: telegram.Bot) -> None:
        from models.proposal import LongProposal
        from tg.stickers import upload_sticker

        is_long = isinstance(proposal, LongProposal)
        model_class = LongPhrase if is_long else Phrase
        repo = self.long_repo if is_long else self.phrase_repo

        phrase = model_class(
            text=proposal.text,
            user_id=proposal.user_id,
            chat_id=proposal.from_chat_id,
            created_at=datetime.now(),
            proposal_id=proposal.id,
        )

        sticker_image = self.create_sticker_image(phrase)
        phrase.sticker_file_id = await upload_sticker(
            bot,
            BytesIO(sticker_image),
            phrase.stickerset_template,
            phrase.stickerset_title_template,
        )
        repo.save(phrase)

    def get_random(self, long: bool = False) -> Phrase:
        repo = self.long_repo if long else self.phrase_repo
        phrases = repo.load_all()
        if not phrases:
            return LongPhrase(text="¡Cuñado!") if long else Phrase(text="¡Cuñado!")
        return random.choice(phrases)

    def get_phrases(self, search: str, long: bool = False) -> list[Phrase | LongPhrase]:
        repo = self.long_repo if long else self.phrase_repo
        phrases = repo.load_all()
        return [p for p in phrases if search.lower() in p.text.lower()]

    def find_most_similar(self, text: str, long: bool = False) -> tuple[Phrase, int]:
        repo = self.long_repo if long else self.phrase_repo
        phrases = repo.load_all()
        if not phrases:
            return (LongPhrase(text="") if long else Phrase(text="")), 0

        norm_text = normalize_str(text)
        return max(
            [(p, fuzz.ratio(norm_text, normalize_str(p.text))) for p in phrases],
            key=lambda x: x[1],
        )

    def register_sticker_usage(self, phrase: Phrase | LongPhrase) -> None:
        """Increments sticker usage counters for a phrase."""
        phrase.usages += 1
        phrase.sticker_usages += 1

        repo = self.long_repo if isinstance(phrase, LongPhrase) else self.phrase_repo
        repo.save(phrase)

    def add_usage_by_id(self, result_id: str) -> None:
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

        repo = self.long_repo if is_long else self.phrase_repo
        # Remove mode prefix
        data = (
            clean_id.replace("long-", "", 1)
            if is_long
            else clean_id.replace("short-", "", 1)
        )

        # In short mode it can be multiple words separated by comma
        texts = data.split(",") if is_short else [data]

        # We need to find the phrases. Since IDs are normalized, we match against normalized text
        all_phrases = repo.load_all()
        for t in texts:
            norm_target = normalize_str(t)
            for p in all_phrases:
                if normalize_str(p.text) == norm_target:
                    p.usages += 1
                    if is_audio:
                        p.audio_usages += 1
                    if is_sticker:
                        p.sticker_usages += 1

                    repo.save(p)
                    break  # Next text
