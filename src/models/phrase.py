import random
from datetime import datetime

import telegram
from fuzzywuzzy import fuzz
from google.cloud import datastore

from utils import improve_punctuation, normalize_str

datastore_client = datastore.Client()


class Phrase:
    kind = "Phrase"
    name = "palabra poderosa / apelativo"
    stickerset_template = "greeting_{}_by_cunhaobot"
    stickerset_title_template = "Saludos cuñadiles {} by @cunhaobot"
    phrases_cache: list["Phrase"] = []

    def __init__(
        self,
        text: str,
        sticker_file_id: str = "",
        usages: int = 0,
        audio_usages: int = 0,
        daily_usages: int = 0,
        audio_daily_usages: int = 0,
        sticker_daily_usages: int = 0,
        sticker_usages: int = 0,
        user_id: int = 0,
        chat_id: int = 0,
        created_at: datetime | None = None,
    ):
        self.text = text
        self.usages = usages
        self.audio_usages = audio_usages
        self.daily_usages = daily_usages
        self.audio_daily_usages = audio_daily_usages
        self.sticker_usages = sticker_usages
        self.sticker_daily_usages = sticker_daily_usages
        self.sticker_file_id = sticker_file_id
        self.user_id = user_id
        self.chat_id = chat_id
        self.created_at = created_at

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.text

    @classmethod
    async def upload_from_proposal(cls, proposal, bot: telegram.Bot):
        phrase = cls(
            text=proposal.text,
            user_id=proposal.user_id,
            chat_id=proposal.from_chat_id,
            created_at=datetime.now(),
        )
        await phrase.generate_sticker(bot)

        phrase.save()

        cls.refresh_cache()
        cls.phrases_cache.append(phrase)

    @classmethod
    def from_entity(cls, entity: datastore.Entity) -> "Phrase":
        return cls(
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
        )

    @classmethod
    def refresh_cache(cls) -> list["Phrase"]:
        query = datastore_client.query(kind=cls.kind)
        cls.phrases_cache = [cls.from_entity(entity) for entity in query.fetch()]

        return cls.phrases_cache

    @classmethod
    def get_phrases(cls, search: str = "", **filters) -> list["Phrase"]:
        if not cls.phrases_cache:
            cls.refresh_cache()

        results = cls.phrases_cache

        if search:
            normalized_search = normalize_str(search)
            results = [
                phrase
                for phrase in results
                if normalized_search in normalize_str(phrase.text)
            ]

        for field, value in filters.items():
            if not value:
                continue

            if value == "__EMPTY__":
                results = [p for p in results if not getattr(p, field)]
            else:
                results = [p for p in results if str(getattr(p, field)) == str(value)]

        return results

    @classmethod
    def get_random_phrase(cls) -> "Phrase":
        return random.choice(cls.get_phrases())

    @classmethod
    def add_usage_by_result_id(cls, result_id: str) -> None:
        match result_id:
            case s if s.startswith("audio-short-"):
                clean_id = s.removeprefix("audio-short-")
                is_audio, is_sticker = True, False
            case s if s.startswith("sticker-short-"):
                clean_id = s.removeprefix("sticker-short-")
                is_audio, is_sticker = False, True
            case s if s.startswith("short-"):
                clean_id = s.removeprefix("short-")
                is_audio, is_sticker = False, False
            case _:
                return

        words = clean_id.split(",")
        phrases = cls.refresh_cache()

        for word in words:
            phrase = next(
                (
                    p
                    for p in phrases
                    if normalize_str(p.text, remove_punctuation=False) == word
                ),
                None,
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
                phrase.save()

    @classmethod
    def remove_daily_usages(cls) -> None:
        query = datastore_client.query(kind=cls.kind)
        entities = [entity for entity in query.fetch()]
        updates = []
        for entity in entities:
            entity["daily_usages"] = 0
            entity["audio_daily_usages"] = 0
            updates.append(entity)

        datastore_client.put_multi(updates)

    @classmethod
    def get_most_similar(cls, text: str) -> tuple["Phrase", int]:
        phrases = cls.get_phrases()
        normalized_input_text = normalize_str(text)

        return max(
            [
                (phrase, fuzz.ratio(normalized_input_text, normalize_str(phrase.text)))
                for phrase in phrases
            ],
            key=lambda x: x[1],
        )

    async def generate_sticker(self, bot: telegram.Bot) -> None:
        from tg.stickers import generate_png, upload_sticker

        sticker_text = f"¿Qué pasa, {self.text}?"
        self.sticker_file_id = await upload_sticker(
            bot,
            generate_png(sticker_text),
            self.stickerset_template,
            self.stickerset_title_template,
        )

    def save(self) -> None:
        key = datastore_client.key(self.kind, self.text)
        phrase_entity = datastore.Entity(key=key)

        phrase_entity["text"] = self.text
        phrase_entity["sticker_file_id"] = self.sticker_file_id
        phrase_entity["usages"] = self.usages
        phrase_entity["audio_usages"] = self.audio_usages
        phrase_entity["sticker_usages"] = self.sticker_usages
        phrase_entity["daily_usages"] = self.daily_usages
        phrase_entity["audio_daily_usages"] = self.audio_daily_usages
        phrase_entity["sticker_daily_usages"] = self.sticker_daily_usages
        phrase_entity["user_id"] = self.user_id
        phrase_entity["chat_id"] = self.chat_id
        phrase_entity["created_at"] = self.created_at

        datastore_client.put(phrase_entity)

    async def edit_text(self, new_text: str, bot: telegram.Bot):
        await self.delete(bot)

        self.text = new_text
        await self.generate_sticker(bot)
        self.save()

    async def delete(self, bot: telegram.Bot) -> None:
        from tg.stickers import delete_sticker

        await delete_sticker(bot, self.sticker_file_id)
        key = datastore_client.key(self.kind, self.text)
        datastore_client.delete(key)


class LongPhrase(Phrase):
    kind = "LongPhrase"
    name = "frase / dicho cuñadíl"
    stickerset_template = "phrase_{}_by_cunhaobot"
    stickerset_title_template = "Frases cuñadiles {} by @cunhaobot"
    phrases_cache: list["Phrase"] = []

    def __init__(self, text, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.text = improve_punctuation(text)

    @classmethod
    def add_usage_by_result_id(cls, result_id: str) -> None:
        if "long-bad-search-" in result_id:
            return

        match result_id:
            case s if s.startswith("audio-long-"):
                clean_id = s.removeprefix("audio-long-")
                is_audio, is_sticker = True, False
            case s if s.startswith("sticker-long-"):
                clean_id = s.removeprefix("sticker-long-")
                is_audio, is_sticker = False, True
            case s if s.startswith("short-"):
                clean_id = s.removeprefix("short-")
                is_audio, is_sticker = False, False
            case _:
                clean_id = result_id
                is_audio, is_sticker = False, False

        normalized_id = normalize_str(clean_id)
        phrases = cls.refresh_cache()

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
            phrase.save()

    async def generate_sticker(self, bot: telegram.Bot) -> None:
        from tg.stickers import generate_png, upload_sticker

        sticker_text = self.text
        self.sticker_file_id = await upload_sticker(
            bot,
            generate_png(sticker_text),
            self.stickerset_template,
            self.stickerset_title_template,
        )
