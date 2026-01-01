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
        entity_id = None
        if entity.key and entity.key.id:
            entity_id = entity.key.id

        return self.model_class(
            id=entity_id,
            text=entity["text"],
            sticker_file_id=entity.get("sticker_file_id", ""),
            usages=entity.get("usages", 0),
            audio_usages=entity.get("audio_usages", 0),
            sticker_usages=entity.get("sticker_usages", 0),
            score=entity.get("score", 0),
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
        if phrase.id:
            key = self.client.key(self.kind, phrase.id)
        else:
            key = self.client.key(self.kind)

        entity = self._domain_to_entity(phrase, key)
        self.client.put(entity)

        if entity.key and entity.key.id:
            phrase.id = entity.key.id

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

    def add_usage(self, phrase_text: str, usage_type: str) -> None:
        # Find phrase by text since ID is now numeric
        phrases = self.get_phrases(search=phrase_text, limit=1)
        # Verify exact match because get_phrases does fuzzy/partial search
        phrase = next((p for p in phrases if p.text == phrase_text), None)

        if phrase:
            phrase.usages += 1
            phrase.score += 1
            if usage_type == "audio":
                phrase.audio_usages += 1
            elif usage_type == "sticker":
                phrase.sticker_usages += 1
            self.save(phrase)

    def add_usage_by_id(self, phrase_id: str | int) -> None:
        phrase = self.load(phrase_id)
        if phrase:
            phrase.usages += 1
            self.save(phrase)

    def get_user_phrase_count(self, user_id: str) -> int:
        """Counts phrases authored by a specific user."""
        try:
            query = self.client.query(kind=self.kind)
            query.add_filter("author_id", "=", str(user_id))
            query.keys_only()
            return len(list(query.fetch(limit=1000)))
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Error counting phrases for user {user_id}: {e}"
            )
            return 0


# Instances
phrase_repository = PhraseDatastoreRepository(Phrase)
long_phrase_repository = PhraseDatastoreRepository(LongPhrase)
