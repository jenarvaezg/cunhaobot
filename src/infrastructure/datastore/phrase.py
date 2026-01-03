import logging
import asyncio
from google.cloud import datastore
from models.phrase import Phrase, LongPhrase
from infrastructure.datastore.base import DatastoreRepository
from utils import normalize_str

logger = logging.getLogger(__name__)


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

    async def load_all(self) -> list[Phrase]:
        if not self._cache:

            def _fetch():
                query = self.client.query(kind=self.kind)
                return [self._entity_to_domain(entity) for entity in query.fetch()]

            self._cache = await asyncio.to_thread(_fetch)
        return self._cache

    async def load(self, entity_id: str | int) -> Phrase | None:
        def _get():
            key = self.get_key(entity_id)
            entity = self.client.get(key)
            return self._entity_to_domain(entity) if entity else None

        return await asyncio.to_thread(_get)

    async def save(self, phrase: Phrase) -> None:
        def _save():
            if phrase.id:
                key = self.client.key(self.kind, phrase.id)
            else:
                key = self.client.key(self.kind)

            entity = self._domain_to_entity(phrase, key)
            self.client.put(entity)

            if entity.key and entity.key.id:
                phrase.id = entity.key.id

        await asyncio.to_thread(_save)
        self._cache = []

    async def get_phrases(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: object
    ) -> list[Phrase]:
        # If cache is populated, use it instead of going to Datastore
        if self._cache:
            results = self._cache
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

        # If there's a search and no cache, we still might need the full load for memory filtering
        if search:
            results = await self.load_all()
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

        # If no search, use Datastore filtering for better performance
        def _fetch():
            query = self.client.query(kind=self.kind)
            for field, value in filters.items():
                if value == "__EMPTY__":
                    # For __EMPTY__ we might still need to filter in memory or check for property existence
                    # For now, let's keep it simple and fallback to full load if __EMPTY__ is used
                    return None
                query.add_filter(field, "=", value)

            # Datastore fetch
            return [
                self._entity_to_domain(entity)
                for entity in query.fetch(
                    limit=limit if limit > 0 else None, offset=offset
                )
            ]

        results_or_none = await asyncio.to_thread(_fetch)
        if results_or_none is not None:
            return results_or_none

        # Fallback to load_all for complex filters or search
        results = await self.load_all()
        for field, value in filters.items():
            if value == "__EMPTY__":
                results = [p for p in results if not getattr(p, field, None)]
            elif value:
                results = [
                    p for p in results if str(getattr(p, field, None)) == str(value)
                ]

        return results[offset : offset + limit] if limit > 0 else results

    async def add_usage(self, phrase_text: str, usage_type: str) -> None:
        # Find phrase by text since ID is now numeric
        phrases = await self.get_phrases(search=phrase_text, limit=1)
        # Verify exact match because get_phrases does fuzzy/partial search
        phrase = next((p for p in phrases if p.text == phrase_text), None)

        if phrase:
            phrase.usages += 1
            phrase.score += 1
            if usage_type == "audio":
                phrase.audio_usages += 1
            elif usage_type == "sticker":
                phrase.sticker_usages += 1
            await self.save(phrase)

    async def add_usage_by_id(self, phrase_id: str | int) -> None:
        phrase = await self.load(phrase_id)
        if phrase:
            phrase.usages += 1
            await self.save(phrase)

    async def get_user_phrase_count(self, user_id: str) -> int:
        """Counts phrases authored by a specific user."""

        def _count():
            try:
                query = self.client.query(kind=self.kind)
                query.add_filter("user_id", "=", str(user_id))

                count_query = self.client.aggregation_query(query=query)
                count_query.count(alias="all")
                results = list(count_query.fetch())
                if results and len(results) > 0 and len(results[0]) > 0:
                    return int(results[0][0].value)
                return 0
            except Exception as e:
                logger.error(f"Error counting phrases for user {user_id}: {e}")
                return 0

        return await asyncio.to_thread(_count)


# Instances
phrase_repository = PhraseDatastoreRepository(Phrase)
long_phrase_repository = PhraseDatastoreRepository(LongPhrase)
