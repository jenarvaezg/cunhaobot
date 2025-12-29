import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Generic, Protocol, TypeVar, cast

import telegram
from fuzzywuzzy import fuzz
from google.cloud import datastore

from utils import improve_punctuation, normalize_str

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="Phrase")


@dataclass(unsafe_hash=True)
class Phrase:
    text: str
    sticker_file_id: str = ""
    usages: int = 0
    audio_usages: int = 0
    daily_usages: int = 0
    audio_daily_usages: int = 0
    sticker_usages: int = 0
    sticker_daily_usages: int = 0
    user_id: int = 0
    chat_id: int = 0
    created_at: datetime | None = None
    proposal_id: str = ""

    # Constants
    kind: ClassVar[str] = "Phrase"
    name: ClassVar[str] = "palabra poderosa / apelativo"
    stickerset_template: ClassVar[str] = "greeting_{}_by_cunhaobot"
    stickerset_title_template: ClassVar[str] = "Saludos cuñadiles {} by @cunhaobot"

    def __str__(self) -> str:
        return self.text

    # --- Domain Logic / Services ---

    async def generate_sticker(self, bot: telegram.Bot) -> None:
        from tg.stickers import generate_png, upload_sticker

        sticker_text = f"¿Qué pasa, {self.text}?"
        self.sticker_file_id = await upload_sticker(
            bot,
            generate_png(sticker_text),
            self.stickerset_template,
            self.stickerset_title_template,
        )

    async def edit_text(self, new_text: str, bot: telegram.Bot) -> None:
        await self.delete(bot)

        self.text = new_text
        await self.generate_sticker(bot)
        self.save()

    async def delete(self, bot: telegram.Bot) -> None:
        from tg.stickers import delete_sticker

        if self.sticker_file_id:
            try:
                await delete_sticker(bot, self.sticker_file_id)
            except Exception as e:
                logger.error(f"Error deleting sticker {self.sticker_file_id}: {e}")

        get_repository(self.__class__).delete(self.text)

    # --- Facade / Active Record style methods (Delegating to Repository) ---

    @classmethod
    def get_repository(cls: type[T]) -> "PhraseRepository[T]":
        return get_repository(cls)

    def save(self) -> None:
        self.get_repository().save(self)

    @classmethod
    async def upload_from_proposal(cls: type[T], proposal, bot: telegram.Bot) -> None:
        phrase = cls(
            text=proposal.text,
            user_id=proposal.user_id,
            chat_id=proposal.from_chat_id,
            created_at=datetime.now(),
            proposal_id=proposal.id,
        )
        await phrase.generate_sticker(bot)
        phrase.save()
        cls.get_repository().refresh_cache()

    @classmethod
    def refresh_cache(cls: type[T]) -> list[T]:
        return cls.get_repository().refresh_cache()

    @classmethod
    def get_phrases(cls: type[T], search: str = "", **filters) -> list[T]:
        return cls.get_repository().get_phrases(search=search, **filters)

    @classmethod
    def get_random_phrase(cls: type[T]) -> T:
        phrases = cls.get_phrases()
        if not phrases:
            return cls(text="¡Cuñado!")
        return random.choice(phrases)

    @classmethod
    def add_usage_by_result_id(cls, result_id: str) -> None:
        cls.get_repository().add_usage_by_result_id(result_id)

    @classmethod
    def remove_daily_usages(cls) -> None:
        cls.get_repository().remove_daily_usages()

    @classmethod
    def get_most_similar(cls: type[T], text: str) -> tuple[T, int]:
        phrases = cls.get_phrases()
        normalized_input_text = normalize_str(text)

        if not phrases:
            return cls(text=""), 0

        return max(
            [
                (phrase, fuzz.ratio(normalized_input_text, normalize_str(phrase.text)))
                for phrase in phrases
            ],
            key=lambda x: x[1],
        )


@dataclass(unsafe_hash=True)
class LongPhrase(Phrase):
    kind: ClassVar[str] = "LongPhrase"
    name: ClassVar[str] = "frase / dicho cuñadíl"
    stickerset_template: ClassVar[str] = "phrase_{}_by_cunhaobot"
    stickerset_title_template: ClassVar[str] = "Frases cuñadiles {} by @cunhaobot"

    def __post_init__(self) -> None:
        self.text = improve_punctuation(self.text)

    async def generate_sticker(self, bot: telegram.Bot) -> None:
        from tg.stickers import generate_png, upload_sticker

        sticker_text = self.text
        self.sticker_file_id = await upload_sticker(
            bot,
            generate_png(sticker_text),
            self.stickerset_template,
            self.stickerset_title_template,
        )


# --- Repository Protocol ---


class PhraseRepository(Generic[T], Protocol):
    def get_all(self) -> list[T]: ...
    def save(self, phrase: T) -> None: ...
    def delete(self, phrase_text: str) -> None: ...
    def refresh_cache(self) -> list[T]: ...
    def get_phrases(self, search: str = "", **filters) -> list[T]: ...
    def add_usage_by_result_id(self, result_id: str) -> None: ...
    def remove_daily_usages(self) -> None: ...


# --- Datastore Implementation ---


class DatastorePhraseRepository(Generic[T]):
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
        self._cache: list[T] = []

    @property
    def client(self) -> datastore.Client:
        return datastore.Client()

    def _entity_to_domain(self, entity: datastore.Entity) -> T:
        return self.model_class(
            text=entity["text"],
            sticker_file_id=entity.get("sticker_file_id", ""),
            usages=entity.get("usages", 0),
            audio_usages=entity.get("audio_usages", 0),
            sticker_usages=entity.get("sticker_usages", 0),
            daily_usages=entity.get("daily_usages", 0),
            audio_daily_usages=entity.get("audio_daily_usages", 0),
            sticker_daily_usages=entity.get("sticker_daily_usages", 0),
            user_id=entity.get("user_id", 0),
            chat_id=entity.get("chat_id", 0),
            created_at=entity.get("created_at"),
            proposal_id=entity.get("proposal_id", ""),
        )

    def _domain_to_entity(self, phrase: T, key: datastore.Key) -> datastore.Entity:
        entity = datastore.Entity(key=key)
        entity.update(
            {
                "text": phrase.text,
                "sticker_file_id": phrase.sticker_file_id,
                "usages": phrase.usages,
                "audio_usages": phrase.audio_usages,
                "sticker_usages": phrase.sticker_usages,
                "daily_usages": phrase.daily_usages,
                "audio_daily_usages": phrase.audio_daily_usages,
                "sticker_daily_usages": phrase.sticker_daily_usages,
                "user_id": phrase.user_id,
                "chat_id": phrase.chat_id,
                "created_at": phrase.created_at,
                "proposal_id": phrase.proposal_id,
            }
        )
        return entity

    def refresh_cache(self) -> list[T]:
        query = self.client.query(kind=self.model_class.kind)
        self._cache = [self._entity_to_domain(entity) for entity in query.fetch()]
        return self._cache

    def get_phrases(self, search: str = "", **filters) -> list[T]:
        if not self._cache:
            self.refresh_cache()

        results = self._cache

        if search:
            normalized_search = normalize_str(search)
            results = [
                phrase
                for phrase in results
                if normalized_search in normalize_str(phrase.text)
            ]

        for field_name, value in filters.items():
            if not value:
                continue

            if value == "__EMPTY__":
                results = [p for p in results if not getattr(p, field_name, None)]
            else:
                results = [
                    p
                    for p in results
                    if str(getattr(p, field_name, None)) == str(value)
                ]

        return results

    def save(self, phrase: T) -> None:
        client = self.client
        key = client.key(self.model_class.kind, phrase.text)
        entity = self._domain_to_entity(phrase, key)
        client.put(entity)

    def delete(self, phrase_text: str) -> None:
        client = self.client
        key = client.key(self.model_class.kind, phrase_text)
        client.delete(key)

    def remove_daily_usages(self) -> None:
        client = self.client
        query = client.query(kind=self.model_class.kind)
        entities = list(query.fetch())

        updates = []
        for entity in entities:
            entity["daily_usages"] = 0
            entity["audio_daily_usages"] = 0
            entity["sticker_daily_usages"] = 0
            updates.append(entity)

        if updates:
            client.put_multi(updates)

    def add_usage_by_result_id(self, result_id: str) -> None:
        is_audio = False
        is_sticker = False
        clean_id = result_id

        if issubclass(self.model_class, Phrase) and not issubclass(
            self.model_class, LongPhrase
        ):
            if result_id.startswith("audio-short-"):
                clean_id = result_id.removeprefix("audio-short-")
                is_audio = True
            elif result_id.startswith("sticker-short-"):
                clean_id = result_id.removeprefix("sticker-short-")
                is_sticker = True
            elif result_id.startswith("short-"):
                clean_id = result_id.removeprefix("short-")
            else:
                return
        else:
            if "long-bad-search-" in result_id:
                return

            if result_id.startswith("audio-long-"):
                clean_id = result_id.removeprefix("audio-long-")
                is_audio = True
            elif result_id.startswith("sticker-long-"):
                clean_id = result_id.removeprefix("sticker-long-")
                is_sticker = True
            elif result_id.startswith("short-"):
                clean_id = result_id.removeprefix("short-")

        words = clean_id.split(",")
        phrases = self.refresh_cache()

        for word in words:
            phrase = None
            if not issubclass(self.model_class, LongPhrase):
                phrase = next(
                    (
                        p
                        for p in phrases
                        if normalize_str(p.text, remove_punctuation=False) == word
                    ),
                    None,
                )
            else:
                normalized_id = normalize_str(clean_id)
                phrase = next(
                    (p for p in phrases if normalized_id in normalize_str(p.text)), None
                )

            if phrase:
                if is_audio:
                    phrase.audio_daily_usages += 1
                    phrase.audio_usages += 1
                elif is_sticker:
                    phrase.sticker_daily_usages += 1
                    phrase.sticker_usages += 1
                else:
                    phrase.daily_usages += 1
                    phrase.usages += 1
                self.save(phrase)

                if issubclass(self.model_class, LongPhrase):
                    break

    def get_all(self) -> list[T]:
        return self.get_phrases()


# --- Dependency Injection / Singleton ---

_phrase_repository: DatastorePhraseRepository[Phrase] = DatastorePhraseRepository(
    Phrase
)
_long_phrase_repository: DatastorePhraseRepository[LongPhrase] = (
    DatastorePhraseRepository(LongPhrase)
)


def get_repository(model_class: type[T]) -> PhraseRepository[T]:
    if issubclass(model_class, LongPhrase):
        return cast(PhraseRepository[T], _long_phrase_repository)
    return cast(PhraseRepository[T], _phrase_repository)
