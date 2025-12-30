import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, date
import pytz
from tg.handlers.commands.ping import handle_ping, _send_report, _send_chapas
from models.schedule import Schedule
from tg.text_router import AUDIO_MODE, STICKER_MODE


class TestPingHandlers:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        yield

    @pytest.mark.asyncio
    async def test_handle_ping_normal_hour(self):
        bot = MagicMock()
        madrid = pytz.timezone("Europe/Madrid")
        mock_now = madrid.localize(datetime(2025, 12, 28, 10, 30, 0))

        with (
            patch("tg.handlers.commands.ping.datetime") as mock_datetime,
            patch("services.schedule_repo.load_all", return_value=[]),
            patch(
                "tg.handlers.commands.ping._send_chapas", new_callable=AsyncMock
            ) as mock_chapas,
        ):
            mock_datetime.now.return_value = mock_now
            await handle_ping(bot)
            mock_chapas.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ping_report_gen(self):
        bot = MagicMock()
        madrid = pytz.timezone("Europe/Madrid")
        mock_now = madrid.localize(datetime(2025, 12, 28, 23, 59, 0))

        with (
            patch("tg.handlers.commands.ping.datetime") as mock_datetime,
            patch("services.schedule_repo.load_all", return_value=[]),
            patch(
                "tg.handlers.commands.ping.report_service.generate_report"
            ) as mock_gen,
            patch("tg.handlers.commands.ping._send_chapas", new_callable=AsyncMock),
            patch("services.phrase_repo.remove_daily_usages") as mock_rm1,
            patch("services.long_phrase_repo.remove_daily_usages") as mock_rm2,
        ):
            mock_datetime.now.return_value = mock_now
            await handle_ping(bot)
            mock_gen.assert_called_once()
            mock_rm1.assert_called_once()
            mock_rm2.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ping_report_send(self):
        bot = MagicMock()
        madrid = pytz.timezone("Europe/Madrid")
        mock_now = madrid.localize(datetime(2025, 12, 28, 7, 0, 0))

        with (
            patch("tg.handlers.commands.ping.datetime") as mock_datetime,
            patch("services.schedule_repo.load_all", return_value=[]),
            patch(
                "tg.handlers.commands.ping._send_report", new_callable=AsyncMock
            ) as mock_send,
            patch("tg.handlers.commands.ping._send_chapas", new_callable=AsyncMock),
        ):
            mock_datetime.now.return_value = mock_now
            await handle_ping(bot)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_report(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        mock_report = MagicMock()
        mock_report.longs = 10
        mock_report.shorts = 5
        mock_report.users = 3
        mock_report.groups = 1
        mock_report.inline_users = 2
        mock_report.inline_usages = 20
        mock_report.gdprs = 0
        mock_report.chapas = 4
        mock_report.top_long = "L"
        mock_report.top_short = "S"

        with patch("services.report_repo.get_at", return_value=mock_report):
            await _send_report(bot, date(2025, 12, 30))
            bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_report_missing(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        with patch("services.report_repo.get_at", return_value=None):
            await _send_report(bot, date(2025, 12, 30))
            bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_chapas_text(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        task = Schedule(chat_id=1, query="text query", hour=10, minute=30, active=True)

        mock_result = MagicMock()
        mock_result.input_message_content.message_text = "Result text"

        # Mock MODE_HANDLERS
        with patch("tg.handlers.commands.ping.MODE_HANDLERS") as handlers:
            # Mock get_query_mode
            with patch(
                "tg.handlers.commands.ping.get_query_mode",
                return_value=("TEXT", "text query"),
            ):
                # Mock result generator
                mock_gen = MagicMock(return_value=iter([mock_result]))
                handlers.get.return_value = mock_gen

                await _send_chapas(bot, [task])

                bot.send_message.assert_called_with(1, "Result text")

    @pytest.mark.asyncio
    async def test_send_chapas_audio(self):
        bot = MagicMock()
        bot.send_voice = AsyncMock()

        task = Schedule(chat_id=1, query="audio query", hour=10, minute=30)

        mock_result = MagicMock()
        mock_result.voice_url = "http://url"

        with patch("tg.handlers.commands.ping.MODE_HANDLERS") as handlers:
            with patch(
                "tg.handlers.commands.ping.get_query_mode",
                return_value=(AUDIO_MODE, "audio query"),
            ):
                mock_gen = MagicMock(return_value=iter([mock_result]))
                handlers.get.return_value = mock_gen

                await _send_chapas(bot, [task])

                bot.send_voice.assert_called_with(1, "http://url")

    @pytest.mark.asyncio
    async def test_send_chapas_sticker(self):
        bot = MagicMock()
        bot.send_sticker = AsyncMock()

        task = Schedule(chat_id=1, query="sticker query", hour=10, minute=30)

        mock_result = MagicMock()
        mock_result.sticker_file_id = "123"

        with patch("tg.handlers.commands.ping.MODE_HANDLERS") as handlers:
            with patch(
                "tg.handlers.commands.ping.get_query_mode",
                return_value=(STICKER_MODE, "sticker query"),
            ):
                mock_gen = MagicMock(return_value=iter([mock_result]))
                handlers.get.return_value = mock_gen

                await _send_chapas(bot, [task])

                bot.send_sticker.assert_called_with(1, "123")

    @pytest.mark.asyncio
    async def test_send_chapas_no_result(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        task = Schedule(chat_id=1, query="bad", hour=10, minute=30)

        with patch("tg.handlers.commands.ping.MODE_HANDLERS") as handlers:
            with patch(
                "tg.handlers.commands.ping.get_query_mode", return_value=("TEXT", "bad")
            ):
                # Empty generator
                mock_gen = MagicMock(return_value=iter([]))
                handlers.get.return_value = mock_gen

                with patch(
                    "tg.handlers.commands.ping.phrase_service.get_random"
                ) as mock_random:
                    mock_random.return_value.text = "random"
                    await _send_chapas(bot, [task])

                    assert bot.send_message.call_count == 2
                    assert (
                        "Te tengo que dar la chapa"
                        in bot.send_message.call_args_list[0][0][1]
                    )

    @pytest.mark.asyncio
    async def test_send_chapas_unknown_mode(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        task = Schedule(chat_id=1, query="unknown", hour=10, minute=30)

        with patch(
            "tg.handlers.commands.ping.get_query_mode",
            return_value=("UNKNOWN", "unknown"),
        ):
            await _send_chapas(bot, [task])
            bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_chapas_error(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        task = Schedule(chat_id=1, query="err", hour=10, minute=30)

        # Raising exception inside loop
        with patch(
            "tg.handlers.commands.ping.get_query_mode", side_effect=Exception("Boom")
        ):
            with patch(
                "tg.handlers.commands.ping.phrase_service.get_random"
            ) as mock_random:
                mock_random.return_value.text = "random"

                await _send_chapas(bot, [task])

                bot.send_message.assert_called_once()  # Error report
                assert "he tenido estos errores" in bot.send_message.call_args[0][1]
