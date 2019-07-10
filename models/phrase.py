import random
from typing import List

from google.cloud import datastore

from utils import normalize_str, improve_punctuation


class Phrase:
    kind = 'Phrase'
    name = 'palabra poderosa / frase corta'

    phrases_cache = []

    def __init__(self, text):
        self.text = text

    @classmethod
    def upload_from_proposal(cls, proposal):
        phrase = cls(proposal.text)
        datastore_client = datastore.Client()

        text = phrase.text
        key = datastore_client.key(cls.kind, text)
        phrase_entity = datastore.Entity(key=key)

        phrase_entity['text'] = text

        cls.refresh_cache()
        datastore_client.put(phrase_entity)
        cls.phrases_cache.append(phrase.text)

    @classmethod
    def from_entity(cls, entity):
        return cls(
            entity['text']
        )

    @classmethod
    def refresh_cache(cls):
        datastore_client = datastore.Client()
        query = datastore_client.query(kind=cls.kind)
        cls.phrases_cache = [cls.from_entity(entity).text for entity in query.fetch()]

    @classmethod
    def get_phrases(cls, search='') -> List[str]:
        if len(cls.phrases_cache) == 0:
            cls.refresh_cache()

        return [phrase for phrase in cls.phrases_cache if normalize_str(search) in normalize_str(phrase)]

    @classmethod
    def get_random_phrase(cls, search='') -> str:
        phrase = cls.get_phrases(search=search) or cls.get_phrases()
        return random.choice(phrase)


class LongPhrase(Phrase):
    kind = 'LongPhrase'
    name = 'frase larga / dicho cuñadíl'

    phrases_cache = []

    def __init__(self, text):
        super().__init__(text)
        self.text = improve_punctuation(text)


