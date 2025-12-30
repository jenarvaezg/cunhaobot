import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal
from services.phrase_service import PhraseService


class TestPhraseService:
    @pytest.fixture
    def service(self):
        self.phrase_repo = MagicMock()
        self.long_repo = MagicMock()
        return PhraseService(self.phrase_repo, self.long_repo)

    @pytest.mark.asyncio
    async def test_create_sticker_image(self, service):
        p = Phrase(text="test")

        with (
            patch("utils.image_utils.generate_png") as mock_png,
        ):
            mock_png.return_value = MagicMock()
            mock_png.return_value.getvalue.return_value = b"png_data"
            img_data = service.create_sticker_image(p)
            assert img_data == b"png_data"
            mock_png.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_sticker_image_long(self, service):
        p = LongPhrase(text="test")

        with (
            patch("utils.image_utils.generate_png") as mock_png,
        ):
            mock_png.return_value = MagicMock()
            mock_png.return_value.getvalue.return_value = b"png_data"
            img_data = service.create_sticker_image(p)
            assert img_data == b"png_data"
            mock_png.assert_called_once()

    def test_get_random(self, service):
        p1 = Phrase(text="foo")
        self.phrase_repo.load_all.return_value = [p1]

        result = service.get_random(long=False)
        assert result == p1

    def test_get_random_empty(self, service):
        self.phrase_repo.load_all.return_value = []
        result = service.get_random(long=False)
        assert result.text == "¡Cuñado!"
        assert isinstance(result, Phrase)

    def test_get_random_long_empty(self, service):
        self.long_repo.load_all.return_value = []
        result = service.get_random(long=True)
        assert result.text == "¡Cuñado!"
        assert isinstance(result, LongPhrase)

    def test_get_phrases(self, service):
        p1 = Phrase(text="hola")
        p2 = Phrase(text="adios")
        self.phrase_repo.load_all.return_value = [p1, p2]

        results = service.get_phrases("hola")
        assert len(results) == 1
        assert results[0] == p1

    def test_find_most_similar(self, service):
        p1 = Phrase(text="hola")
        p2 = Phrase(text="adios")
        self.phrase_repo.load_all.return_value = [p1, p2]

        result, score = service.find_most_similar("holaa")
        assert result == p1
        assert score > 80

    def test_find_most_similar_empty(self, service):
        self.phrase_repo.load_all.return_value = []
        result, score = service.find_most_similar("holaa")
        assert result.text == ""
        assert score == 0
        assert isinstance(result, Phrase)

    def test_find_most_similar_long_empty(self, service):
        self.long_repo.load_all.return_value = []
        result, score = service.find_most_similar("holaa", long=True)
        assert result.text == ""
        assert score == 0
        assert isinstance(result, LongPhrase)

    def test_register_sticker_usage(self, service):
        p = Phrase(text="test")
        service.register_sticker_usage(p)
        assert p.usages == 1
        assert p.sticker_usages == 1
        self.phrase_repo.save.assert_called_once_with(p)

    @pytest.mark.asyncio
    async def test_create_from_proposal(self, service):
        mock_bot = MagicMock()
        proposal = Proposal(id="1", text="prop", user_id=1, from_chat_id=2)

        # Mock create_sticker_image internal call
        with (
            patch.object(service, "create_sticker_image", return_value=b"img"),
            patch("tg.stickers.upload_sticker", new_callable=AsyncMock) as mock_upload,
        ):
            mock_upload.return_value = "sticker_123"
            await service.create_from_proposal(proposal, mock_bot)

            service.phrase_repo.save.assert_called_once()
            saved_phrase = service.phrase_repo.save.call_args[0][0]
            assert isinstance(saved_phrase, Phrase)
            assert saved_phrase.text == "prop"
            assert saved_phrase.sticker_file_id == "sticker_123"

    @pytest.mark.asyncio
    async def test_create_from_proposal_long(self, service):
        mock_bot = MagicMock()
        proposal = LongProposal(id="1", text="prop", user_id=1, from_chat_id=2)

        with (
            patch.object(service, "create_sticker_image", return_value=b"img"),
            patch("tg.stickers.upload_sticker", new_callable=AsyncMock) as mock_upload,
        ):
            mock_upload.return_value = "sticker_123"
            await service.create_from_proposal(proposal, mock_bot)

            service.long_repo.save.assert_called_once()
            saved_phrase = service.long_repo.save.call_args[0][0]
            assert isinstance(saved_phrase, LongPhrase)
            assert saved_phrase.text == "prop"
            assert saved_phrase.sticker_file_id == "sticker_123"

    def test_add_usage_by_id_short_text(self, service):
        p1 = Phrase(text="foo")
        service.phrase_repo.load_all.return_value = [p1]

        service.add_usage_by_id("short-foo")

        assert p1.usages == 1
        service.phrase_repo.save.assert_called_once_with(p1)

    def test_add_usage_by_id_short_combination(self, service):
        p1 = Phrase(text="foo")
        p2 = Phrase(text="bar")
        service.phrase_repo.load_all.return_value = [p1, p2]

        service.add_usage_by_id("short-foo,bar")

        assert p1.usages == 1
        assert p2.usages == 1
        assert service.phrase_repo.save.call_count == 2

    def test_add_usage_by_id_long_audio(self, service):
        p1 = LongPhrase(text="long phrase")
        service.long_repo.load_all.return_value = [p1]

        service.add_usage_by_id("audio-long-long phrase")

        assert p1.usages == 1
        assert p1.audio_usages == 1
        service.long_repo.save.assert_called_once_with(p1)

    def test_add_usage_by_id_short_sticker(self, service):
        p1 = Phrase(text="sticker text")
        service.phrase_repo.load_all.return_value = [p1]

        service.add_usage_by_id("sticker-short-sticker text")

        assert p1.usages == 1
        assert p1.sticker_usages == 1
        service.phrase_repo.save.assert_called_once_with(p1)

    def test_add_usage_by_id_invalid(self, service):
        service.add_usage_by_id("invalid-id")
        service.phrase_repo.save.assert_not_called()
        service.long_repo.save.assert_not_called()
