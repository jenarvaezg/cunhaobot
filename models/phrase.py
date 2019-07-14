import random
from typing import List, Optional, Tuple

from fuzzywuzzy import fuzz
from google.cloud import datastore

from utils import normalize_str, improve_punctuation

datastore_client = datastore.Client()


class Phrase:
    kind = 'Phrase'
    name = 'palabra poderosa / apelativo'

    phrases_cache = []

    def __init__(self, text, usages=0, audio_usages=0, daily_usages=0, audio_daily_usages=0):
        self.text = text
        self.usages = usages
        self.audio_usages = audio_usages
        self.daily_usages = daily_usages
        self.audio_daily_usages = audio_daily_usages

    @classmethod
    def upload_from_proposal(cls, proposal):
        phrase = cls(proposal.text)
        phrase.save()

        cls.refresh_cache()
        cls.phrases_cache.append(phrase.text)

    @classmethod
    def from_entity(cls, entity):
        return cls(
            entity['text'],
            entity.get('usages', 0),
            entity.get('audio_usages', 0),
            entity.get('daily_usages', 0),
            entity.get('audio_daily_usages', 0),
        )

    @classmethod
    def refresh_cache(cls) -> List['Phrase']:
        query = datastore_client.query(kind=cls.kind)
        instances = [cls.from_entity(entity) for entity in query.fetch()]
        cls.phrases_cache = [i.text for i in instances]

        return instances

    @classmethod
    def get_phrases(cls, search='') -> List[str]:
        if len(cls.phrases_cache) == 0:
            cls.refresh_cache()

        return [phrase for phrase in cls.phrases_cache if normalize_str(search) in normalize_str(phrase)]

    @classmethod
    def get_random_phrase(cls, search='') -> str:
        phrase = cls.get_phrases(search=search) or cls.get_phrases()
        return random.choice(phrase)

    @classmethod
    def add_usage_by_result_id(cls, result_id: str) -> None:
        is_audio = result_id.startswith('audio-')
        result_id = normalize_str(result_id[len('audio-short-'):] if is_audio else result_id[len('short-'):])
        words = result_id.split(", ")
        phrases = cls.refresh_cache()

        for word in words:
            phrase: Optional['Phrase'] = next(iter(p for p in phrases if normalize_str(p.text) == word), None)
            if phrase:
                if is_audio:
                    phrase.audio_daily_usages += 1
                    phrase.audio_usages += 1
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
    def get_most_similar(cls, text: str) -> Tuple[str, int]:
        phrases = cls.get_phrases()
        normalized_input_text = normalize_str(text)

        return max(
            ((phrase, fuzz.ratio(normalized_input_text, normalize_str(phrase))) for phrase in phrases),
            key=lambda x: x[1],
        )

    def save(self) -> None:
        key = datastore_client.key(self.kind, self.text)
        phrase_entity = datastore.Entity(key=key)

        phrase_entity['text'] = self.text
        phrase_entity['usages'] = self.usages
        phrase_entity['audio_usages'] = self.audio_usages
        phrase_entity['daily_usages'] = self.daily_usages
        phrase_entity['audio_daily_usages'] = self.audio_daily_usages

        datastore_client.put(phrase_entity)


class LongPhrase(Phrase):
    kind = 'LongPhrase'
    name = 'frase / dicho cuñadíl'

    phrases_cache = []

    def __init__(self, text, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.text = improve_punctuation(text)

    @classmethod
    def add_usage_by_result_id(cls, result_id: str) -> None:
        if 'long-bad-search-' in result_id:
            return

        is_audio = result_id.startswith('audio-')
        result_id = result_id[len('audio-long-'):] if is_audio else result_id[len('long-'):]
        phrases = cls.refresh_cache()

        phrase: Optional['Phrase'] = next(iter(
            p for p in phrases if result_id in normalize_str(p.text)
        ), None)

        if phrase:
            if is_audio:
                phrase.audio_daily_usages += 1
                phrase.audio_usages += 1
            else:
                phrase.daily_usages += 1
                phrase.usages += 1
            phrase.save()

