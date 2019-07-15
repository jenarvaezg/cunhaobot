import random
from typing import List, Optional, Tuple

import telegram
from fuzzywuzzy import fuzz
from google.cloud import datastore

from tg.stickers import generate_png, upload_sticker, delete_sticker
from utils import normalize_str, improve_punctuation

datastore_client = datastore.Client()


class Phrase:
    kind = 'Phrase'
    name = 'palabra poderosa / apelativo'
    stickerset_template = 'greeting_{}_by_cunhaobot'
    stickerset_title_template = 'Saludos cuñadiles {} by @cunhaobot'
    phrases_cache = []

    def __init__(
            self, text, sticker_file_id='', usages=0, audio_usages=0, daily_usages=0, audio_daily_usages=0,
            sticker_daily_usages=0, sticker_usages=0):
        self.text = text
        self.usages = usages
        self.audio_usages = audio_usages
        self.daily_usages = daily_usages
        self.audio_daily_usages = audio_daily_usages
        self.sticker_usages = sticker_usages
        self.sticker_daily_usages = sticker_daily_usages
        self.sticker_file_id = sticker_file_id

    def __str__(self) -> str:
        return self.text

    @classmethod
    def upload_from_proposal(cls, proposal, bot: telegram.Bot):
        phrase = cls(proposal.text)
        phrase.generate_sticker(bot)

        phrase.save()

        cls.refresh_cache()
        cls.phrases_cache.append(phrase)

    @classmethod
    def from_entity(cls, entity):
        return cls(
            entity['text'],
            sticker_file_id=entity.get('sticker_file_id', 0),
            usages=entity.get('usages', 0),
            audio_usages=entity.get('audio_usages', 0),
            sticker_usages=entity.get('sticker_usages', 0),
            daily_usages=entity.get('daily_usages', 0),
            audio_daily_usages=entity.get('audio_daily_usages', 0),
            sticker_daily_usages=entity.get('sticker_daily_usages', 0),
        )

    @classmethod
    def refresh_cache(cls) -> List['Phrase']:
        query = datastore_client.query(kind=cls.kind)
        instances = [cls.from_entity(entity) for entity in query.fetch()]
        cls.phrases_cache = [i.text for i in instances]

        return instances

    @classmethod
    def get_phrases(cls, search='') -> List['Phrase']:
        if len(cls.phrases_cache) == 0:
            cls.refresh_cache()

        return [phrase for phrase in cls.phrases_cache if normalize_str(search) in normalize_str(phrase)]

    @classmethod
    def get_random_phrase(cls, search='') -> 'Phrase':
        phrase = cls.get_phrases(search=search) or cls.get_phrases()
        return random.choice(phrase)

    @classmethod
    def add_usage_by_result_id(cls, result_id: str) -> None:
        is_audio = result_id.startswith('audio-')
        is_sticker = result_id.startswith('sticker-')

        if is_audio:
            result_id = result_id[len('audio-short-'):]
        elif is_sticker:
            result_id = result_id[len('sticker-short-'):]
        else:
            result_id = result_id[len('short-'):]

        result_id = normalize_str(result_id)
        words = result_id.split(", ")
        phrases = cls.refresh_cache()

        for word in words:
            phrase: Optional['Phrase'] = next(iter(p for p in phrases if normalize_str(p.text) == word), None)
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
            entity['daily_usages'] = 0
            entity['audio_daily_usages'] = 0
            updates.append(entity)

        datastore_client.put_multi(updates)

    @classmethod
    def get_most_similar(cls, text: str) -> Tuple['Phrase', int]:
        phrases = cls.get_phrases()
        normalized_input_text = normalize_str(text)

        return max(
            [(phrase, fuzz.WRatio(normalized_input_text, normalize_str(phrase))) for phrase in phrases],
            key=lambda x: x[1],
        )

    def generate_sticker(self, bot: telegram.Bot) -> None:
        sticker_text = f"¿Qué pasa, {self.text}?"
        self.sticker_file_id = upload_sticker(
                bot, generate_png(sticker_text), self.stickerset_template, self.stickerset_title_template
        )

    def save(self) -> None:
        key = datastore_client.key(self.kind, self.text)
        phrase_entity = datastore.Entity(key=key)

        phrase_entity['text'] = self.text
        phrase_entity['sticker_file_id'] = self.sticker_file_id
        phrase_entity['usages'] = self.usages
        phrase_entity['audio_usages'] = self.audio_usages
        phrase_entity['sticker_usages'] = self.sticker_usages
        phrase_entity['daily_usages'] = self.daily_usages
        phrase_entity['audio_daily_usages'] = self.audio_daily_usages
        phrase_entity['sticker_daily_usages'] = self.sticker_daily_usages

        datastore_client.put(phrase_entity)

    def edit_text(self, new_text: str, bot: telegram.Bot):
        self.delete(bot)

        self.text = new_text
        self.generate_sticker(bot)
        self.save()

    def delete(self, bot: telegram.Bot) -> None:
        delete_sticker(bot, self.sticker_file_id)
        key = datastore_client.key(self.kind, self.text)
        datastore_client.delete(key)


class LongPhrase(Phrase):
    kind = 'LongPhrase'
    name = 'frase / dicho cuñadíl'
    stickerset_template = 'phrase_{}_by_cunhaobot'
    stickerset_title_template = 'Frases cuñadiles {} by @cunhaobot'
    phrases_cache = []

    def __init__(self, text, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.text = improve_punctuation(text)

    @classmethod
    def add_usage_by_result_id(cls, result_id: str) -> None:
        if 'long-bad-search-' in result_id:
            return

        is_sticker = result_id.startswith('sticker-')
        is_audio = result_id.startswith('audio-')

        if is_audio:
            result_id = result_id[len('audio-long-'):]
        elif is_sticker:
            result_id = result_id[len('sticker-long-'):]
        else:
            result_id = result_id[len('short-'):]

        result_id = normalize_str(result_id)
        phrases = cls.refresh_cache()

        phrase: Optional['Phrase'] = next(iter(
            p for p in phrases if result_id in normalize_str(p.text)
        ), None)

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

    def generate_sticker(self, bot: telegram.Bot) -> None:
        sticker_text = self.text
        self.sticker_file_id = upload_sticker(
            bot, generate_png(sticker_text), self.stickerset_template, self.stickerset_title_template
        )
