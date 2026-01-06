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
                    # Fallback to full load if __EMPTY__ is used
                    return None

                # Normalize numeric strings to int for better DB matching
                val = value
                if isinstance(value, str) and value.isdigit():
                    val = int(value)

                query.add_filter(filter=datastore.query.PropertyFilter(field, "=", val))

            # Datastore fetch
            return [
                self._entity_to_domain(entity)
                for entity in query.fetch(
                    limit=limit if limit > 0 else None, offset=offset
                )
            ]

        results_or_none = await asyncio.to_thread(_fetch)
        if results_or_none is not None:
            # Fallback: if we filtered by user_id and got 0 results, try string ID
            user_id_filter = filters.get("user_id")
            if not results_or_none and user_id_filter and str(user_id_filter).isdigit():

                def _fetch_string_fallback():
                    q = self.client.query(kind=self.kind)
                    q.add_filter(
                        filter=datastore.query.PropertyFilter(
                            "user_id", "=", str(user_id_filter)
                        )
                    )
                    return [
                        self._entity_to_domain(e)
                        for e in q.fetch(limit=limit if limit > 0 else None)
                    ]

                results_or_none = await asyncio.to_thread(_fetch_string_fallback)

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

    async def get_user_phrase_count(self, user_id: str | int) -> int:
        """Counts phrases authored by a specific user."""

        def _count():
            try:
                # Try numeric ID first
                uid = user_id
                if isinstance(user_id, str) and user_id.isdigit():
                    uid = int(user_id)

                query = self.client.query(kind=self.kind)
                query.add_filter(
                    filter=datastore.query.PropertyFilter("user_id", "=", uid)
                )

                count_query = self.client.aggregation_query(query=query)
                count_query.count(alias="all")
                results = list(count_query.fetch())
                if results and len(results) > 0 and len(results[0]) > 0:
                    count = int(results[0][0].value)
                    if count > 0:
                        return count

                # Try string fallback
                query2 = self.client.query(kind=self.kind)
                query2.add_filter(
                    filter=datastore.query.PropertyFilter("user_id", "=", str(uid))
                )
                count_query2 = self.client.aggregation_query(query=query2)
                count_query2.count(alias="all")
                results2 = list(count_query2.fetch())
                if results2 and len(results2) > 0 and len(results2[0]) > 0:
                    return int(results2[0][0].value)

                return 0
            except Exception as e:
                logger.error(f"Error counting phrases for user {user_id}: {e}")
                return 0

        return await asyncio.to_thread(_count)


# Instances
phrase_repository = PhraseDatastoreRepository(Phrase)
long_phrase_repository = PhraseDatastoreRepository(LongPhrase)
