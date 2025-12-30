import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.stickers import (
    upload_sticker,
    delete_sticker,
)
from utils.image_utils import (
    generate_png,
    _text_wrap,
    _draw_text_with_border,
)
import io


class TestStickers:
    def test_text_wrap(self):
        mock_font = MagicMock()
        mock_font.getbbox.side_effect = lambda x: (0, 0, len(x) * 10, 20)

        text = "one two three four"
        lines = _text_wrap(text, mock_font, 50)
        assert len(lines) > 1

    def test_draw_text_with_border(self):
        mock_draw = MagicMock()
        mock_font = MagicMock()
        _draw_text_with_border("test", (0, 0), mock_font, mock_draw)
        assert mock_draw.text.call_count == 5

    def test_generate_png(self):
        text = "Test Phrase"
        result = generate_png(text)
        assert isinstance(result, io.BytesIO)

    def test_generate_png_long_word(self):
        # Trigger line 35-36 in stickers.py (if not line: line = words[i])
        generate_png("a" * 100)

    def test_generate_png_font_none(self):
        # Actually, let's just mock the loop to not run by mocking range
        with patch("utils.image_utils.range", return_value=[]):
            with pytest.raises(ValueError, match="Could not calculate font size"):
                generate_png("test")

    @pytest.mark.asyncio
    async def test_upload_sticker_existing_set(self):
        bot = MagicMock()
        bot.upload_sticker_file = AsyncMock(return_value=MagicMock(file_id="new_file"))
        bot.get_sticker_set = AsyncMock()
        bot.add_sticker_to_set = AsyncMock()

        mock_set_before = MagicMock()
        mock_set_before.stickers = [MagicMock(file_id="old_id")]

        mock_set_after = MagicMock()
        mock_set_after.stickers = [
            MagicMock(file_id="old_id"),
            MagicMock(file_id="new_sticker_id"),
        ]

        bot.get_sticker_set.side_effect = [mock_set_before, mock_set_after]

        res = await upload_sticker(bot, io.BytesIO(b"png"), "tmpl_{}", "title {}")
        assert res == "new_sticker_id"
        bot.add_sticker_to_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_sticker_set_full_retry(self):
        # From final_push_test.py
        bot = MagicMock()
        bot.upload_sticker_file = AsyncMock(return_value=MagicMock(file_id="f"))
        bot.get_sticker_set = AsyncMock()

        import telegram
        import io

        # 1. offset 1 -> Stickers_too_much
        # 2. offset 2 -> Stickerset_invalid -> Create new
        # 3. end -> get_sticker_set
        bot.get_sticker_set.side_effect = [
            telegram.error.BadRequest("Stickers_too_much"),
            telegram.error.BadRequest("Stickerset_invalid"),
            MagicMock(stickers=[MagicMock(file_id="new")]),
        ]
        bot.add_sticker_to_set = AsyncMock()
        bot.create_new_sticker_set = AsyncMock()

        res = await upload_sticker(bot, io.BytesIO(b"p"), "t_{}", "T {}")
        assert res == "new"
        assert bot.get_sticker_set.call_count == 3

    @pytest.mark.asyncio
    async def test_delete_sticker(self):
        bot = MagicMock()
        bot.delete_sticker_from_set = AsyncMock()
        await delete_sticker(bot, "file_id")
        bot.delete_sticker_from_set.assert_called_once_with("file_id")
