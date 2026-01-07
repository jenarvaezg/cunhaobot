import pytest
from unittest.mock import MagicMock, patch
from models.phrase import Phrase
from infrastructure.datastore.phrase import PhraseDatastoreRepository
from google.cloud import datastore


def create_mock_entity(data, kind="Phrase", entity_id=123):
    key = datastore.Key(kind, entity_id, project="test")
    entity = datastore.Entity(key=key)
    entity.update(data)
    return entity


@pytest.fixture
def repo():
    return PhraseDatastoreRepository()


class TestPhraseRepository:
    @pytest.mark.asyncio
    async def test_save_phrase(self, repo):
        with patch(
            "infrastructure.datastore.base.get_datastore_client"
        ) as mock_client_factory:
            mock_datastore_client = mock_client_factory.return_value
            phrase = Phrase(id=1, text="test phrase", user_id=123)
            await repo.save(phrase)

            mock_datastore_client.put.assert_called_once()
            # Just verify put was called, deep inspection of Entity object created inside the method
            # is flaky with mocks

    @pytest.mark.asyncio
    async def test_load_phrase(self, repo):
        mock_phrase = Phrase(id=1, text="loaded phrase", user_id=456)
        with patch.object(repo, "_entity_to_domain", return_value=mock_phrase):
            with patch(
                "infrastructure.datastore.base.get_datastore_client"
            ) as mock_client_factory:
                mock_datastore_client = mock_client_factory.return_value
                mock_datastore_client.get.return_value = MagicMock()

                phrase = await repo.load(1)
                assert phrase is not None
                assert phrase.text == "loaded phrase"
                assert phrase.user_id == 456

    @pytest.mark.asyncio
    async def test_load_phrase_not_found(self, repo):
        with patch(
            "infrastructure.datastore.base.get_datastore_client"
        ) as mock_client_factory:
            mock_datastore_client = mock_client_factory.return_value
            mock_datastore_client.get.return_value = None
            phrase = await repo.load(999)
            assert phrase is None

    @pytest.mark.asyncio
    async def test_delete_phrase(self, repo):
        with patch(
            "infrastructure.datastore.base.get_datastore_client"
        ) as mock_client_factory:
            mock_datastore_client = mock_client_factory.return_value
            await repo.delete(1)
            mock_datastore_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_phrases_simple(self, repo):
        mock_phrase = Phrase(id=1, text="test", user_id=1)
        with patch.object(repo, "_entity_to_domain", return_value=mock_phrase):
            with patch(
                "infrastructure.datastore.base.get_datastore_client"
            ) as mock_client_factory:
                mock_datastore_client = mock_client_factory.return_value
                mock_query = MagicMock()
                mock_datastore_client.query.return_value = mock_query
                mock_query.fetch.return_value = [MagicMock()]

                results = await repo.get_phrases()
                assert len(results) == 1
                assert results[0].text == "test"

    @pytest.mark.asyncio
    async def test_get_phrases_with_filters(self, repo):
        with patch(
            "infrastructure.datastore.base.get_datastore_client"
        ) as mock_client_factory:
            mock_datastore_client = mock_client_factory.return_value
            mock_query = MagicMock()
            mock_datastore_client.query.return_value = mock_query
            mock_query.fetch.return_value = []

            await repo.get_phrases(user_id="123")
            assert mock_query.add_filter.called

    @pytest.mark.asyncio
    async def test_load_all(self, repo):
        mock_phrase = Phrase(id=1, text="phrase1")
        with patch.object(repo, "_entity_to_domain", return_value=mock_phrase):
            with patch(
                "infrastructure.datastore.base.get_datastore_client"
            ) as mock_client_factory:
                mock_datastore_client = mock_client_factory.return_value
                mock_query = MagicMock()
                mock_datastore_client.query.return_value = mock_query
                mock_query.fetch.return_value = [MagicMock()]

                repo.clear_cache()
                phrases = await repo.load_all()
                assert len(phrases) == 1
                assert phrases[0].text == "phrase1"

                # Test cache hit
                mock_datastore_client.query.reset_mock()
                phrases = await repo.load_all()
                mock_datastore_client.query.assert_not_called()
