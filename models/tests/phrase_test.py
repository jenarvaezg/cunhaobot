import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

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

    @pytest.mark.asyncio
    async def test_upload_from_proposal(self):
        mock_bot = MagicMock()
        mock_proposal = MagicMock()
        mock_proposal.text = "proposal text"
        mock_proposal.user_id = 123
        mock_proposal.from_chat_id = 456

        with (
            patch("tg.stickers.generate_png") as mock_png,
            patch("tg.stickers.upload_sticker", new_callable=AsyncMock) as mock_upload,
            patch.object(Phrase, "save") as mock_save,
            patch.object(Phrase, "refresh_cache") as mock_refresh,
        ):
            await Phrase.upload_from_proposal(mock_proposal, mock_bot)
            mock_png.assert_called_once()
            mock_upload.assert_called_once()
            mock_save.assert_called_once()
            mock_refresh.assert_called_once()

    def test_phrase_str(self):
        p = Phrase(text="hola")
        assert str(p) == "hola"
        assert repr(p) == "hola"
        mock_query = MagicMock()
        self.mock_client.query.return_value = mock_query
        # Ensure we hit the inner lines by providing an entity with the key
        entity1 = {"text": "p1", "daily_usages": 5, "audio_daily_usages": 2}
        mock_query.fetch.return_value = [entity1]

        Phrase.remove_daily_usages()
        assert entity1["daily_usages"] == 0
        assert entity1["audio_daily_usages"] == 0
        self.mock_client.put_multi.assert_called_once()

    def test_add_usage_by_result_id_invalid(self):
        with patch.object(Phrase, "refresh_cache") as mock_refresh:
            Phrase.add_usage_by_result_id("invalid-id")
            mock_refresh.assert_not_called()

    def test_add_usage_by_result_id_long_default(self):
        p1 = LongPhrase(text="long phrase")
        with (
            patch.object(LongPhrase, "save"),
            patch.object(LongPhrase, "refresh_cache", return_value=[p1]),
        ):
            # default case
            LongPhrase.add_usage_by_result_id("long-phrase")
            assert p1.daily_usages == 1

    def test_get_most_similar(self):
        p1 = Phrase(text="hola")
        p2 = Phrase(text="adios")
        Phrase.phrases_cache = [p1, p2]

        result, score = Phrase.get_most_similar("holaa")
        assert result == p1
        assert score > 80

    @pytest.mark.asyncio
    async def test_generate_sticker(self):
        mock_bot = MagicMock()
        p = Phrase(text="test")

        with (
            patch("tg.stickers.generate_png") as mock_png,
            patch("tg.stickers.upload_sticker", new_callable=AsyncMock) as mock_upload,
        ):
            mock_upload.return_value = "file_id_123"
            await p.generate_sticker(mock_bot)
            assert p.sticker_file_id == "file_id_123"
            mock_png.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_text(self):
        mock_bot = MagicMock()
        p = Phrase(text="old")

        with (
            patch.object(Phrase, "delete", new_callable=AsyncMock) as mock_delete,
            patch.object(
                Phrase, "generate_sticker", new_callable=AsyncMock
            ) as mock_gen,
            patch.object(Phrase, "save") as mock_save,
        ):
            await p.edit_text("new", mock_bot)
            assert p.text == "new"
            mock_delete.assert_called_once_with(mock_bot)
            mock_gen.assert_called_once_with(mock_bot)
            mock_save.assert_called_once()


class TestLongPhrase:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        LongPhrase.phrases_cache = []
        self.mock_client = mock_datastore_client
        self.mock_client.reset_mock()
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

    def test_add_usage_by_result_id_long(self):
        p1 = LongPhrase(text="long phrase one")

        with (
            patch.object(LongPhrase, "save"),
            patch.object(LongPhrase, "refresh_cache", return_value=[p1]),
        ):
            # Bad search case
            LongPhrase.add_usage_by_result_id("long-bad-search-xxx")
            assert p1.daily_usages == 0

            # Audio case
            LongPhrase.add_usage_by_result_id("audio-long-phrase-one")
            assert p1.audio_daily_usages == 1

            # Sticker case
            LongPhrase.add_usage_by_result_id("sticker-long-phrase-one")
            assert p1.sticker_daily_usages == 1

            # Normal case
            LongPhrase.add_usage_by_result_id("short-phrase-one")
            assert p1.daily_usages == 1

    def test_phrase_random_sample_draw(self):
        # Coverage for shuffle logic in ping.py?
        # No, just cover Phrase class methods.
        pass

    @pytest.mark.asyncio
    async def test_generate_sticker_long(self):
        mock_bot = MagicMock()
        lp = LongPhrase(text="test long")

        with (
            patch("tg.stickers.generate_png"),
            patch("tg.stickers.upload_sticker", new_callable=AsyncMock) as mock_upload,
        ):
            mock_upload.return_value = "file_id_long"
            await lp.generate_sticker(mock_bot)
            assert lp.sticker_file_id == "file_id_long"
            mock_upload.assert_called_once()
