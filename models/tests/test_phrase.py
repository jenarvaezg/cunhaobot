import asyncio
from unittest.mock import MagicMock, patch

import pytest

# Import models.phrase - this will use the mocked datastore from conftest.py
from models.phrase import LongPhrase, Phrase


class TestPhrase:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Reset the cache and mock calls before each test
        Phrase.phrases_cache = []
        LongPhrase.phrases_cache = []

        # Get the mock client from the imported module
        from models.phrase import datastore_client

        datastore_client.reset_mock()
        self.mock_client = datastore_client

        yield

    def test_from_entity(self):
        entity = {"text": "test phrase", "usages": 5, "sticker_file_id": "123"}
        phrase = Phrase.from_entity(entity)
        assert phrase.text == "test phrase"
        assert phrase.usages == 5
        assert phrase.sticker_file_id == "123"
        assert phrase.audio_usages == 0  # Default

    def test_refresh_cache(self):
        # Setup mock query
        mock_query = MagicMock()
        self.mock_client.query.return_value = mock_query

        entity1 = {"text": "phrase1"}
        entity2 = {"text": "phrase2"}
        mock_query.fetch.return_value = [entity1, entity2]

        phrases = Phrase.refresh_cache()

        # Check query was called with correct kind
        self.mock_client.query.assert_called_with(kind="Phrase")
        assert len(phrases) == 2
        assert phrases[0].text == "phrase1"
        assert phrases[1].text == "phrase2"
        assert Phrase.phrases_cache == phrases

    def test_get_phrases(self):
        p1 = Phrase(text="foo")
        p2 = Phrase(text="bar")
        Phrase.phrases_cache = [p1, p2]

        # Test empty search returns all
        assert Phrase.get_phrases() == [p1, p2]

        # Test search
        assert Phrase.get_phrases("fo") == [p1]
        assert Phrase.get_phrases("ba") == [p2]
        assert Phrase.get_phrases("z") == []

    def test_get_random_phrase(self):
        p1 = Phrase(text="foo")
        Phrase.phrases_cache = [p1]

        assert Phrase.get_random_phrase() == p1

    def test_add_usage_by_result_id(self):
        # Setup cache
        p1 = Phrase(text="phrase1")
        p2 = Phrase(text="phrase2")

        # Prepare mock save (we mock the method on the class or instance)
        # Since p1 and p2 are instances, we can spy on their save method?
        # Easier to mock Phrase.save globally or on instance.

        with (
            patch.object(Phrase, "save") as mock_save,
            patch.object(Phrase, "refresh_cache", return_value=[p1, p2]),
        ):
            # Case 1: Standard usage
            Phrase.add_usage_by_result_id("short-phrase1")
            assert p1.daily_usages == 1
            assert p1.usages == 1
            mock_save.assert_called()

            # Case 2: Audio usage
            Phrase.add_usage_by_result_id("audio-short-phrase2")
            assert p2.audio_daily_usages == 1
            assert p2.audio_usages == 1

            # Case 3: Sticker usage
            Phrase.add_usage_by_result_id("sticker-short-phrase1")
            assert p1.sticker_daily_usages == 1
            assert p1.sticker_usages == 1

    def test_save(self):
        p = Phrase(text="test", usages=1)

        # Mock datastore key and entity
        mock_key = MagicMock()
        self.mock_client.key.return_value = mock_key

        # We need to ensure datastore.Entity is mocked or works.
        # In conftest, we mocked google.cloud.datastore.
        # So datastore.Entity is a Mock class.

        p.save()

        self.mock_client.key.assert_called_with("Phrase", "test")
        self.mock_client.put.assert_called()

        # Check that the entity was created/populated
        # Since Entity is a mock, the constructor call returns a mock.
        # We can check if put was called with that mock.

        # However, checking dictionary assignment on a mock is tricky if not configured.
        # But we can at least verify put() was called.

    @pytest.mark.asyncio
    async def test_delete(self):
        p = Phrase(text="test")
        p.sticker_file_id = "sticker123"

        mock_bot = MagicMock()

        # Mock tg.stickers.delete_sticker which is imported inside delete()
        with patch("tg.stickers.delete_sticker") as mock_delete_sticker:
            f = asyncio.Future()
            f.set_result(None)
            mock_delete_sticker.return_value = f

            await p.delete(mock_bot)

            mock_delete_sticker.assert_called_with(mock_bot, "sticker123")
            self.mock_client.key.assert_called_with("Phrase", "test")
            self.mock_client.delete.assert_called()


class TestLongPhrase:
    @pytest.fixture(autouse=True)
    def setup(self):
        LongPhrase.phrases_cache = []
        from models.phrase import datastore_client

        datastore_client.reset_mock()
        self.mock_client = datastore_client
        yield

    def test_init_improves_punctuation(self):
        lp = LongPhrase(text="hello world")
        assert lp.text == "Hello world."

    def test_refresh_cache_long(self):
        mock_query = MagicMock()
        self.mock_client.query.return_value = mock_query

        entity1 = {"text": "long phrase 1"}
        mock_query.fetch.return_value = [entity1]

        phrases = LongPhrase.refresh_cache()

        self.mock_client.query.assert_called_with(kind="LongPhrase")
        assert len(phrases) == 1
        assert isinstance(phrases[0], LongPhrase)
