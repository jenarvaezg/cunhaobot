from unittest.mock import MagicMock
import pytest
from models.phrase import Phrase, LongPhrase
from infrastructure.datastore.phrase import PhraseDatastoreRepository
from datetime import datetime


def create_mock_entity(data, kind="Phrase", entity_id=12345):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get

    def setitem(key, value):
        data[key] = value

    m.__setitem__.side_effect = setitem
    m.update.side_effect = data.update
    m.key.kind = kind

    if isinstance(entity_id, int):
        m.key.id = entity_id
        m.key.name = None
    else:
        m.key.name = entity_id
        m.key.id = None

    return m


class TestPhraseRepository:
    @pytest.fixture
    def repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        return PhraseDatastoreRepository(Phrase)

    @pytest.fixture
    def long_repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        return PhraseDatastoreRepository(LongPhrase)

    def test_entity_to_domain_with_defaults(self, repo):
        # Test default values for missing fields
        data = {"text": "default phrase"}
        entity = create_mock_entity(data)

        phrase = repo._entity_to_domain(entity)
        assert phrase.text == "default phrase"
        assert phrase.usages == 0
        assert phrase.sticker_file_id == ""
        assert phrase.audio_usages == 0
        assert phrase.sticker_usages == 0
        assert phrase.score == 0
        assert phrase.user_id == 0
        assert phrase.chat_id == 0
        assert phrase.created_at is None
        assert phrase.proposal_id == ""

    def test_entity_to_domain_with_all_fields(self, repo):
        now = datetime.now()
        data = {
            "text": "full phrase",
            "sticker_file_id": "sticker123",
            "usages": 10,
            "audio_usages": 5,
            "sticker_usages": 2,
            "score": 100,
            "user_id": 123,
            "chat_id": 456,
            "created_at": now,
            "proposal_id": "prop999",
        }
        entity = create_mock_entity(data)
        phrase = repo._entity_to_domain(entity)
        assert phrase.text == "full phrase"
        assert phrase.sticker_file_id == "sticker123"
        assert phrase.usages == 10
        assert phrase.audio_usages == 5
        assert phrase.sticker_usages == 2
        assert phrase.score == 100
        assert phrase.user_id == 123
        assert phrase.chat_id == 456
        assert phrase.created_at == now
        assert phrase.proposal_id == "prop999"

    @pytest.mark.asyncio
    async def test_load_all(self, repo, mock_datastore_client):
        mock_query = MagicMock()
        mock_datastore_client.query.return_value = mock_query

        entity1 = create_mock_entity({"text": "phrase1"})
        mock_query.fetch.return_value = [entity1]

        phrases = await repo.load_all()
        assert len(phrases) == 1
        assert phrases[0].text == "phrase1"
        mock_datastore_client.query.assert_called_with(kind="Phrase")

        # Test cache hit
        mock_datastore_client.query.reset_mock()
        phrases = await repo.load_all()
        mock_datastore_client.query.assert_not_called()  # Should not be called again

    @pytest.mark.asyncio
    async def test_load_not_found(self, repo, mock_datastore_client):
        mock_datastore_client.get.return_value = None
        phrase = await repo.load("non_existent")
        assert phrase is None
        mock_datastore_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_clears_cache(self, repo, mock_datastore_client):
        # Populate cache
        repo._cache = [Phrase(text="cached")]
        p = Phrase(text="new_phrase", usages=1)
        await repo.save(p)
        assert not repo._cache  # Cache should be cleared
        mock_datastore_client.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_phrases_with_empty_filter(self, repo):
        p1 = Phrase(text="phrase 1", proposal_id="prop1")
        p2 = Phrase(text="phrase 2", proposal_id="")
        repo._cache = [p1, p2]

        results = await repo.get_phrases(proposal_id="__EMPTY__")
        assert len(results) == 1
        assert results[0].text == "phrase 2"

    @pytest.mark.asyncio
    async def test_get_phrases_with_value_filter_and_limit(self, repo):
        p1 = Phrase(text="foo", usages=10, chat_id=123)
        p2 = Phrase(text="bar", usages=5, chat_id=456)
        p3 = Phrase(text="foobar", usages=15, chat_id=123)
        repo._cache = [p1, p2, p3]

        results = await repo.get_phrases(search="foo", limit=1)
        assert len(results) == 1
        assert results[0].text in [
            "foo",
            "foobar",
        ]  # Order might vary depending on initial cache order

        results = await repo.get_phrases(usages=10)
        assert len(results) == 1
        assert results[0].text == "foo"

        results = await repo.get_phrases(chat_id=123)
        assert len(results) == 2
        assert {p.text for p in results} == {"foo", "foobar"}

        results = await repo.get_phrases(chat_id="456")  # Test string conversion
        assert len(results) == 1
        assert results[0].text == "bar"

        results = await repo.get_phrases(limit=2, offset=1)
        assert len(results) == 2
        assert results[0].text == "bar"
        assert results[1].text == "foobar"

    @pytest.mark.asyncio
    async def test_get_phrases_filter(self, repo, mock_datastore_client):
        p1 = Phrase(text="foo", proposal_id="123")
        p2 = Phrase(text="bar", proposal_id="")
        repo._cache = [p1, p2]

        # Test __EMPTY__ filter
        results = await repo.get_phrases(proposal_id="__EMPTY__")
        assert len(results) == 1
        assert results[0].text == "bar"

        # Test value filter
        results = await repo.get_phrases(proposal_id="123")
        assert len(results) == 1
        assert results[0].text == "foo"

    @pytest.mark.asyncio
    async def test_add_usage(self, repo, mock_datastore_client):
        p1 = Phrase(text="target", usages=5, score=10)
        repo._cache = [p1]

        await repo.add_usage("target", "audio")

        assert p1.usages == 6
        assert p1.audio_usages == 1
        assert p1.score == 11
        mock_datastore_client.put.assert_called_once()
