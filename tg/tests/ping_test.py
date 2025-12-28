import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, date
import pytz
from tg.handlers.ping import handle_ping, _send_chapas, _generate_report, _send_report
from models.schedule import ScheduledTask
from models.report import Report


class TestPingHandlers:
    @pytest.fixture(autouse=True)
    def setup(self):
        from models.phrase import Phrase, LongPhrase, datastore_client

        Phrase.phrases_cache = []
        LongPhrase.phrases_cache = []
        datastore_client.reset_mock()
        datastore_client.query.return_value.fetch.return_value = []

        # Mock random phrase generation
        self.patcher_phrase = patch(
            "models.phrase.Phrase.get_random_phrase", return_value="cuñao"
        )
        self.mock_phrase = self.patcher_phrase.start()

        # Mock ScheduledTask.get_tasks globally for ping tests
        self.patcher_tasks = patch(
            "models.schedule.ScheduledTask.get_tasks", return_value=[]
        )
        self.patcher_tasks.start()

        yield
        self.patcher_phrase.stop()
        self.patcher_tasks.stop()

    @pytest.mark.asyncio
    async def test_handle_ping_normal_hour(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        # Mock datetime.now() to a normal hour
        madrid = pytz.timezone("Europe/Madrid")
        mock_now = madrid.localize(datetime(2025, 12, 28, 12, 0, 0))

        with (
            patch("tg.handlers.ping.datetime") as mock_datetime,
            patch(
                "tg.handlers.ping._send_chapas", new_callable=AsyncMock
            ) as mock_chapas,
        ):
            mock_datetime.now.return_value = mock_now

            await handle_ping(bot)

            mock_chapas.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ping_report_gen(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        madrid = pytz.timezone("Europe/Madrid")
        mock_now = madrid.localize(datetime(2025, 12, 28, 23, 59, 0))

        with (
            patch("tg.handlers.ping.datetime") as mock_datetime,
            patch("tg.handlers.ping._generate_report") as mock_gen,
            patch("tg.handlers.ping._send_chapas", new_callable=AsyncMock),
        ):
            mock_datetime.now.return_value = mock_now

            await handle_ping(bot)

            mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ping_report_send(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        madrid = pytz.timezone("Europe/Madrid")
        mock_now = madrid.localize(datetime(2025, 12, 28, 7, 0, 0))

        with (
            patch("tg.handlers.ping.datetime") as mock_datetime,
            patch("tg.handlers.ping._send_report", new_callable=AsyncMock) as mock_send,
            patch("tg.handlers.ping._send_chapas", new_callable=AsyncMock),
        ):
            mock_datetime.now.return_value = mock_now

            await handle_ping(bot)

            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_chapas_success(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        task = MagicMock(spec=ScheduledTask)
        task.query = "short test"
        task.chat_id = 123

        mock_result = MagicMock()
        mock_result.id = "short-test"
        mock_result.input_message_content.message_text = "chapa text"

        with (
            patch("tg.handlers.ping.get_query_mode", return_value=("SHORT", "test")),
            patch("tg.handlers.ping.MODE_HANDLERS", {"SHORT": lambda x: [mock_result]}),
        ):
            await _send_chapas(bot, [task])
            bot.send_message.assert_called_with(123, "chapa text")

    @pytest.mark.asyncio
    async def test_send_chapas_not_found(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()
        task = MagicMock(spec=ScheduledTask)
        task.query = "unknown"
        task.chat_id = 123

        with (
            patch("tg.handlers.ping.get_query_mode", return_value=("SHORT", "unknown")),
            patch("tg.handlers.ping.MODE_HANDLERS", {"SHORT": lambda x: []}),
            patch("models.phrase.LongPhrase.get_random_phrase") as mock_random,
        ):
            mock_random.return_value.text = "random phrase"
            await _send_chapas(bot, [task])
            assert bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_send_chapas_no_func(self):
        # From missing_lines_test.py
        task = MagicMock()
        task.query = "unknown"
        bot = MagicMock()
        with patch("tg.handlers.ping.get_query_mode", return_value=("UNKNOWN", "rest")):
            await _send_chapas(bot, [task])
            # Should continue without error

    @pytest.mark.asyncio
    async def test_send_chapas_error_path(self):
        # From final_push_test.py
        bot = MagicMock()
        bot.send_message = AsyncMock()
        task = MagicMock()
        task.query = "error"
        task.datastore_id = "task_id"

        # Populate cache to avoid refresh_cache hitting the mock
        from models.phrase import Phrase

        Phrase.phrases_cache = [Phrase(text="p1")]

        # Forzamos una excepción en get_query_mode
        with patch("tg.handlers.ping.get_query_mode", side_effect=Exception("boom")):
            await _send_chapas(bot, [task])
            # Debería haber enviado un reporte de error a los curadores
            bot.send_message.assert_called()
            assert "errores" in bot.send_message.call_args[0][1]

    @pytest.mark.asyncio
    async def test_send_chapas_audio_sticker(self):
        # From final_push_test.py
        bot = MagicMock()
        bot.send_voice = AsyncMock()
        bot.send_sticker = AsyncMock()

        task_audio = MagicMock(query="audio test", chat_id=1)
        task_sticker = MagicMock(query="sticker test", chat_id=2)

        res_audio = MagicMock(voice_url="http://v")
        res_sticker = MagicMock(sticker_file_id="s123")

        with (
            patch("tg.handlers.ping.get_query_mode") as mock_mode,
            patch("tg.handlers.ping.MODE_HANDLERS") as mock_handlers,
        ):
            mock_mode.side_effect = [("AUDIO", ""), ("STICKER", "")]
            mock_handlers.get.side_effect = [
                lambda x: [res_audio],
                lambda x: [res_sticker],
            ]

            await _send_chapas(bot, [task_audio, task_sticker])
            bot.send_voice.assert_called_once()
            bot.send_sticker.assert_called_once()

    def test_generate_report(self):
        # We need to mock get_tasks specifically here since we patched it in setup
        with (
            patch("models.phrase.LongPhrase.refresh_cache", return_value=[]),
            patch("models.phrase.Phrase.refresh_cache", return_value=[]),
            patch("models.user.User.load_all", return_value=[]),
            patch("models.schedule.ScheduledTask.get_tasks", return_value=[]),
            patch("models.user.InlineUser.get_all", return_value=[]),
            patch("models.report.Report.generate") as mock_gen,
            patch("models.phrase.Phrase.remove_daily_usages") as mock_rem1,
            patch("models.phrase.LongPhrase.remove_daily_usages") as mock_rem2,
        ):
            _generate_report(date(2025, 12, 28))
            mock_gen.assert_called_once()
            mock_rem1.assert_called_once()
            mock_rem2.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_report(self):
        bot = MagicMock()
        bot.send_message = AsyncMock()

        mock_report = MagicMock(spec=Report)
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

        with patch("models.report.Report.get_at", return_value=mock_report):
            await _send_report(bot, date(2025, 12, 28))
            bot.send_message.assert_called_once()
            args, _ = bot.send_message.call_args
            assert "Resumen del 2025/12/27" in args[1]
