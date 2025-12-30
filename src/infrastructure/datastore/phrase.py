from typing import Any
from google.cloud import datastore
from models.phrase import Phrase, LongPhrase
from infrastructure.datastore.base import DatastoreRepository
from utils import normalize_str


class PhraseDatastoreRepository(DatastoreRepository[Phrase]):
    def __init__(self, model_class: type[Phrase] | type[LongPhrase] = Phrase):
        super().__init__(model_class.kind)
        self.model_class = model_class
        self._cache: list[Phrase] = []

    def _entity_to_domain(self, entity: datastore.Entity) -> Phrase:
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

    def _domain_to_entity(self, phrase: Phrase, key: datastore.Key) -> datastore.Entity:
        entity = datastore.Entity(key=key)
        entity.update(phrase.model_dump())
        return entity

    def load_all(self) -> list[Phrase]:
        if not self._cache:
            query = self.client.query(kind=self.kind)
            self._cache = [self._entity_to_domain(entity) for entity in query.fetch()]
        return self._cache

    def load(self, entity_id: str | int) -> Phrase | None:
        key = self.get_key(entity_id)
        entity = self.client.get(key)
        return self._entity_to_domain(entity) if entity else None

    def save(self, phrase: Phrase) -> None:
        key = self.get_key(phrase.text)
        entity = self._domain_to_entity(phrase, key)
        self.client.put(entity)
        self._cache = []

    def get_phrases(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: Any
    ) -> list[Phrase]:
        results = self.load_all()
        if search:
            norm_search = normalize_str(search)
            results = [p for p in results if norm_search in normalize_str(p.text)]

        for field, value in filters.items():
            if value == "__EMPTY__":
                results = [p for p in results if not getattr(p, field, None)]
            elif value:
                results = [
                    p for p in results if str(getattr(p, field, None)) == str(value)
                ]

        return results[offset : offset + limit] if limit > 0 else results

    def remove_daily_usages(self) -> None:
        query = self.client.query(kind=self.kind)
        entities = list(query.fetch())
        for entity in entities:
            entity["daily_usages"] = 0
            entity["audio_daily_usages"] = 0
            entity["sticker_daily_usages"] = 0
        if entities:
            self.client.put_multi(entities)
            self._cache = []


# Instances
phrase_repository = PhraseDatastoreRepository(Phrase)
long_phrase_repository = PhraseDatastoreRepository(LongPhrase)
