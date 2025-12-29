import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import models.phrase - this will use the mocked datastore from conftest.py
from models.phrase import LongPhrase, Phrase, DatastorePhraseRepository


def create_mock_entity(data):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get

    # Allow item assignment to update the underlying dict?
    # For tests that do entity['field'] = val, we might need __setitem__
    def setitem(key, value):
        data[key] = value

    m.__setitem__.side_effect = setitem
    m.update.side_effect = data.update
    return m


class TestPhrase:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        # Reset the cache and mock calls before each test
        Phrase.get_repository()._cache = []
        LongPhrase.get_repository()._cache = []

        mock_datastore_client.reset_mock()
        self.mock_client = mock_datastore_client

        yield

    def test_from_entity(self):
        # Test the repository's mapper
        repo = Phrase.get_repository()
        if isinstance(repo, DatastorePhraseRepository):
            data = {"text": "test phrase", "usages": 5, "sticker_file_id": "123"}
            entity = create_mock_entity(data)

            phrase = repo._entity_to_domain(entity)
            assert phrase.text == "test phrase"
            assert phrase.usages == 5
            assert phrase.sticker_file_id == "123"
            assert phrase.audio_usages == 0  # Default

    def test_refresh_cache(self):
        # Setup mock query
        mock_query = MagicMock()
        self.mock_client.query.return_value = mock_query

        entity1 = create_mock_entity({"text": "phrase1"})
        entity2 = create_mock_entity({"text": "phrase2"})

        mock_query.fetch.return_value = [entity1, entity2]

        phrases = Phrase.refresh_cache()

        # Check query was called with correct kind
        self.mock_client.query.assert_called_with(kind="Phrase")
        assert len(phrases) == 2
        assert phrases[0].text == "phrase1"
        assert phrases[1].text == "phrase2"
        # The cache is populated with domain objects
        assert Phrase.get_repository()._cache == phrases

    def test_get_phrases(self):
        p1 = Phrase(text="foo", sticker_file_id="s1")
        p2 = Phrase(text="bar", sticker_file_id="")
        Phrase.get_repository()._cache = [p1, p2]

        assert Phrase.get_phrases() == [p1, p2]

        assert Phrase.get_phrases("fo") == [p1]
        assert Phrase.get_phrases("ba") == [p2]
        assert Phrase.get_phrases("z") == []

        # Test field filters
        assert Phrase.get_phrases(sticker_file_id="s1") == [p1]
        assert Phrase.get_phrases(sticker_file_id="__EMPTY__") == [p2]
        assert Phrase.get_phrases(non_existent_field=None) == [p1, p2]

    def test_get_random_phrase(self):
        p1 = Phrase(text="foo")
        Phrase.get_repository()._cache = [p1]

        assert Phrase.get_random_phrase() == p1

    def test_add_usage_by_result_id(self):
        # Setup cache
        p1 = Phrase(text="phrase1")
        p2 = Phrase(text="phrase2")

        repo = Phrase.get_repository()
        repo._cache = [p1, p2]

        with (
            patch.object(repo, "save") as mock_save,
            patch.object(repo, "refresh_cache", return_value=[p1, p2]),
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

        p.save()

        self.mock_client.key.assert_called_with("Phrase", "test")
        self.mock_client.put.assert_called()

    @pytest.mark.asyncio
    async def test_delete(self):
        p = Phrase(text="test")
        p.sticker_file_id = "sticker123"

        mock_bot = MagicMock()

        # Patch the repository delete to check it's called
        with (
            patch("tg.stickers.delete_sticker") as mock_delete_sticker,
            patch.object(Phrase.get_repository(), "delete") as mock_repo_delete,
        ):
            f = asyncio.Future()
            f.set_result(None)
            mock_delete_sticker.return_value = f

            await p.delete(mock_bot)

            mock_delete_sticker.assert_called_with(mock_bot, "sticker123")
            mock_repo_delete.assert_called_with("test")

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
            patch.object(DatastorePhraseRepository, "save") as mock_save,
            patch.object(DatastorePhraseRepository, "refresh_cache") as mock_refresh,
        ):
            await Phrase.upload_from_proposal(mock_proposal, mock_bot)
            mock_png.assert_called_once()
            mock_upload.assert_called_once()
            mock_save.assert_called_once()
            mock_refresh.assert_called_once()

    def test_phrase_str(self):
        p = Phrase(text="hola")
        assert str(p) == "hola"

        # Test remove_daily_usages
        mock_query = MagicMock()
        self.mock_client.query.return_value = mock_query

        data = {"text": "p1", "daily_usages": 5, "audio_daily_usages": 2}
        entity1 = create_mock_entity(data)
        mock_query.fetch.return_value = [entity1]

        Phrase.remove_daily_usages()
        assert data["daily_usages"] == 0
        assert data["audio_daily_usages"] == 0
        self.mock_client.put_multi.assert_called_once()

    def test_add_usage_by_result_id_invalid(self):
        repo = Phrase.get_repository()
        with patch.object(repo, "refresh_cache") as mock_refresh:
            Phrase.add_usage_by_result_id("short-invalid-id")
            mock_refresh.assert_called()

    def test_add_usage_by_result_id_long_default(self):
        p1 = LongPhrase(text="long phrase")
        repo = LongPhrase.get_repository()
        repo._cache = [p1]

        with (
            patch.object(repo, "save"),
            patch.object(repo, "refresh_cache", return_value=[p1]),
        ):
            # default case
            # Original logic: "long-phrase" (without prefix) -> treated as clean_id
            # My new logic: if not starts with prefix, clean_id = result_id
            # But LongPhrase matches "normalized_id in normalize_str(p.text)"

            LongPhrase.add_usage_by_result_id("long-phrase")
            assert p1.daily_usages == 1

    def test_get_most_similar(self):
        p1 = Phrase(text="hola")
        p2 = Phrase(text="adios")
        Phrase.get_repository()._cache = [p1, p2]

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

        # Need to mock delete and save
        repo = Phrase.get_repository()

        with (
            patch.object(p, "delete", new_callable=AsyncMock) as mock_delete,
            patch.object(p, "generate_sticker", new_callable=AsyncMock) as mock_gen,
            patch.object(repo, "save") as mock_save,
        ):
            await p.edit_text("new", mock_bot)
            assert p.text == "new"
            mock_delete.assert_called_once_with(mock_bot)
            mock_gen.assert_called_once_with(mock_bot)
            mock_save.assert_called_once()


class TestLongPhrase:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        LongPhrase.get_repository()._cache = []
        self.mock_client = mock_datastore_client
        self.mock_client.reset_mock()
        yield

    def test_init_improves_punctuation(self):
        lp = LongPhrase(text="hello world")
        assert lp.text == "Hello world."

    def test_refresh_cache_long(self):
        mock_query = MagicMock()
        self.mock_client.query.return_value = mock_query

        entity1 = create_mock_entity({"text": "long phrase 1"})
        mock_query.fetch.return_value = [entity1]

        phrases = LongPhrase.refresh_cache()

        self.mock_client.query.assert_called_with(kind="LongPhrase")
        assert len(phrases) == 1
        assert isinstance(phrases[0], LongPhrase)

    def test_add_usage_by_result_id_long(self):
        p1 = LongPhrase(text="long phrase one")
        repo = LongPhrase.get_repository()
        repo._cache = [p1]

        with (
            patch.object(repo, "save"),
            patch.object(repo, "refresh_cache", return_value=[p1]),
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
