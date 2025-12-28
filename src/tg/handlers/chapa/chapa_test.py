import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.chapa.create import (
    handle_create_chapa,
    require_valid_query,
    split_time,
)
from tg.handlers.chapa.delete import handle_delete_chapa, handle_delete_chapas
from tg.handlers.chapa.list import handle_list_chapas
from models.schedule import ScheduledTask
from telegram import Chat


class TestChapaHandlers:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        self.patcher_phrase = patch(
            "models.phrase.Phrase.get_random_phrase", return_value="cuñao"
        )
        self.mock_phrase = self.patcher_phrase.start()
        from models.phrase import Phrase, LongPhrase

        Phrase.phrases_cache = []
        LongPhrase.phrases_cache = []
        mock_datastore_client.reset_mock()
        # Ensure refresh_cache doesn't crash if called
        mock_datastore_client.query.return_value.fetch.return_value = []
        yield
        self.patcher_phrase.stop()

    def test_require_valid_query_invalid(self):
        with (
            patch(
                "tg.handlers.chapa.create.get_query_mode",
                return_value=("INVALID", "rest"),
            ),
            patch("tg.handlers.chapa.create.MODE_HANDLERS", {}),
        ):
            with pytest.raises(KeyError):
                require_valid_query("query")

    def test_split_time_invalid_hour(self):
        with pytest.raises(ValueError, match="Mal valor de horas"):
            split_time("2500")
        with pytest.raises(ValueError, match="Mal valor de horas"):
            split_time("-0100")

    def test_split_time_invalid_minute(self):
        with pytest.raises(ValueError, match="Mal valor de minutos"):
            split_time("1065")

    def test_split_time_basura(self):
        with pytest.raises(ValueError, match="basura"):
            split_time("abc")

    @pytest.mark.asyncio
    async def test_handle_create_chapa_no_message(self):
        update = MagicMock()
        update.effective_message = None
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        await handle_create_chapa(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_create_chapa_no_chat(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 frase"
        update.effective_chat = None
        await handle_create_chapa(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_create_chapa_usage_return(self):
        update = MagicMock()
        update.effective_message.text = "/chapa"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        # admin check
        with patch("tg.decorators.only_admins", lambda x: x):
            await handle_create_chapa(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_create_chapa_no_chat_return(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 frase"
        update.effective_chat = None
        # This will fail only admins first
        with patch("tg.decorators.only_admins", lambda x: x):
            await handle_create_chapa(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_create_chapa_key_error(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 frase"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        with patch(
            "tg.handlers.chapa.create.require_valid_query", side_effect=KeyError("err")
        ):
            await handle_create_chapa(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_create_chapa_success(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 frase"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.id = 123
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE

        with patch("models.schedule.ScheduledTask.save") as mock_save:
            await handle_create_chapa(update, MagicMock())
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_delete_chapas_with_args(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapas some_arg"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        await handle_delete_chapas(update, MagicMock())
        update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_delete_chapas_no_tasks(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapas"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        with patch("models.schedule.ScheduledTask.get_tasks", return_value=[]):
            await handle_delete_chapas(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_delete_chapas_success(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapas"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        mock_task = MagicMock()
        with patch("models.schedule.ScheduledTask.get_tasks", return_value=[mock_task]):
            await handle_delete_chapas(update, MagicMock())
            mock_task.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_usage_return(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapa"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        await handle_delete_chapa(update, MagicMock())
        update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_no_tasks_return(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapa 1"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        with patch("models.schedule.ScheduledTask.get_tasks", return_value=[]):
            await handle_delete_chapa(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_no_chat_return(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapa 1"
        update.effective_chat = None
        await handle_delete_chapa(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_usage(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapa"  # length 1
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        await handle_delete_chapa(update, MagicMock())
        update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_no_tasks(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapa 1"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        with patch("models.schedule.ScheduledTask.get_tasks", return_value=[]):
            await handle_delete_chapa(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_success(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapa 1"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        mock_task = MagicMock()
        with patch("models.schedule.ScheduledTask.get_tasks", return_value=[mock_task]):
            await handle_delete_chapa(update, MagicMock())
            mock_task.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_not_found_index(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapa 1"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.id = 123
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        with patch("models.schedule.ScheduledTask.get_tasks", return_value=[]):
            await handle_delete_chapa(update, MagicMock())
            assert (
                "no te estoy dando la chapa"
                in update.effective_message.reply_text.call_args[0][0]
            )

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_index_error(self):
        update = MagicMock()
        update.effective_message.text = "/borrarchapa 10"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.id = 123
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        with patch(
            "models.schedule.ScheduledTask.get_tasks", return_value=[MagicMock()]
        ):
            await handle_delete_chapa(update, MagicMock())
            assert "pasado" in update.effective_message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_create_chapa_invalid_query_keyerror(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 query"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        with patch(
            "tg.handlers.chapa.create.get_query_mode", return_value=("INVALID", "rest")
        ):
            await handle_create_chapa(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_no_message_return(self):
        update = MagicMock()
        update.effective_message = None
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        await handle_delete_chapa(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_create_chapa_no_text_return(self):
        # From chapa_test.py (previous addition)
        update = MagicMock()
        update.effective_message.text = None

        inner_func = handle_create_chapa
        while hasattr(inner_func, "__wrapped__"):
            inner_func = inner_func.__wrapped__
        await inner_func(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_create_chapa_no_chat_return_line72(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 query"
        update.effective_chat = None

        inner_func = handle_create_chapa
        while hasattr(inner_func, "__wrapped__"):
            inner_func = inner_func.__wrapped__
        await inner_func(update, MagicMock())

    def test_split_time_errors_extra(self):
        with pytest.raises(ValueError, match="basura"):
            split_time("abc")
        with pytest.raises(ValueError, match="minutos"):
            split_time("1099")
        with pytest.raises(ValueError, match="horas"):
            split_time("9900")

    @pytest.mark.asyncio
    async def test_handle_create_chapa_key_error_block(self):
        # From last_push_test.py
        from models.phrase import Phrase

        Phrase.phrases_cache = [Phrase(text="p1")]

        update = MagicMock()
        update.effective_message.text = "/chapa 1030 query"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = "private"
        update.effective_chat.PRIVATE = "private"

        with patch("tg.handlers.chapa.create.split_time", side_effect=KeyError("err")):
            await handle_create_chapa(update, MagicMock())
            assert update.effective_message.reply_text.call_count >= 1

    @pytest.mark.asyncio
    async def test_handle_list_chapas_empty(self):
        # From misc_handlers_test.py
        update = MagicMock()
        update.effective_chat.id = 456
        update.effective_message.reply_text = AsyncMock()
        context = MagicMock()

        with patch("models.schedule.ScheduledTask.get_tasks", return_value=[]):
            await handle_list_chapas(update, context)
            update.effective_message.reply_text.assert_called()
            args, _ = update.effective_message.reply_text.call_args
            assert "No has configurado chapas" in args[0]

    @pytest.mark.asyncio
    async def test_handle_list_chapas_success(self):
        # From misc_handlers_test.py
        update = MagicMock()
        update.effective_chat.id = 456
        update.effective_message.reply_text = AsyncMock()
        context = MagicMock()

        mock_task = MagicMock(spec=ScheduledTask)
        mock_task.__str__.return_value = "task info"
        with patch("models.schedule.ScheduledTask.get_tasks", return_value=[mock_task]):
            await handle_list_chapas(update, context)
            update.effective_message.reply_text.assert_called()
            args, _ = update.effective_message.reply_text.call_args
            assert "task info" in args[0]

    @pytest.mark.asyncio
    async def test_handle_create_chapa_split_exception(self):
        # From missing_lines_test.py
        from models.phrase import Phrase

        Phrase.phrases_cache = [Phrase(text="p1")]
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 query"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE

        # Bypass decorators
        inner_func = handle_create_chapa
        while hasattr(inner_func, "__wrapped__"):
            inner_func = inner_func.__wrapped__

        with patch(
            "tg.handlers.chapa.create.split_time",
            side_effect=ValueError("forced error"),
        ):
            await inner_func(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_create_chapa_key_error_exception(self):
        # From missing_lines_test.py
        from models.phrase import Phrase

        Phrase.phrases_cache = [Phrase(text="p1")]
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 query"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE

        inner_func = handle_create_chapa
        while hasattr(inner_func, "__wrapped__"):
            inner_func = inner_func.__wrapped__

        with patch(
            "tg.handlers.chapa.create.require_valid_query",
            side_effect=KeyError("forced error"),
        ):
            await inner_func(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_create_chapa_index_error_exception(self):
        # From missing_lines_test.py
        from models.phrase import Phrase

        Phrase.phrases_cache = [Phrase(text="p1")]
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 query"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE

        inner_func = handle_create_chapa
        while hasattr(inner_func, "__wrapped__"):
            inner_func = inner_func.__wrapped__

        with patch(
            "tg.handlers.chapa.create.split_time",
            side_effect=IndexError("forced error"),
        ):
            await inner_func(update, MagicMock())
            update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_create_chapa_no_message_return_extra(self):
        # From missing_lines_test.py
        update = MagicMock(effective_message=None)
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        await handle_create_chapa(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_create_chapa_split_error_extra(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message.text = "/chapa extra space"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.type = Chat.PRIVATE
        update.effective_chat.PRIVATE = Chat.PRIVATE
        await handle_create_chapa(update, MagicMock())
        update.effective_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_no_chat_return_line49_extra(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message.text = "/borrarchapa 1"
        update.effective_chat = None
        # Bypass only_admins
        with patch("tg.decorators.only_admins", lambda x: x):
            await handle_delete_chapa(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_no_chat_return_line58_fixed_extra(self):
        # From missing_lines_test.py
        update = MagicMock()
        update.effective_message.text = "/borrarchapa 1"
        update.effective_chat = None

        func = handle_delete_chapa
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__
        await func(update, MagicMock())
