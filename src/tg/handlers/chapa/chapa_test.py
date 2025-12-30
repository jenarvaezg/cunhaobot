import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import Chat
from tg.handlers.chapa.create import handle_create_chapa, usage
from tg.handlers.chapa.delete import handle_delete_chapa
from tg.handlers.chapa.list import handle_list_chapas
from models.phrase import Phrase


class TestChapaHandlers:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        self.mock_client = mock_datastore_client
        yield

    @pytest.mark.asyncio
    async def test_usage_no_message(self):
        update = MagicMock()
        update.effective_message = None
        with pytest.raises(ValueError, match="No effective message"):
            await usage(update)

    @pytest.mark.asyncio
    async def test_handle_create_chapa_usage(self):
        update = MagicMock()
        update.effective_message.text = "/chapa"
        update.effective_message.reply_text = AsyncMock()

        mock_phrase = Phrase(text="cuñao")
        with patch(
            "tg.handlers.chapa.create.phrase_service.get_random",
            return_value=mock_phrase,
        ):
            await handle_create_chapa.__wrapped__.__wrapped__(update, MagicMock())
            # Should call usage -> reply_text
            update.effective_message.reply_text.assert_called_once()
            assert (
                "Para usar el servicio de chapas"
                in update.effective_message.reply_text.call_args[0][0]
            )

    @pytest.mark.asyncio
    async def test_handle_create_chapa_invalid_time(self):
        update = MagicMock()
        update.effective_message.text = "/chapa badtime"
        update.effective_message.reply_text = AsyncMock()

        mock_phrase = Phrase(text="cuñao")
        with patch(
            "tg.handlers.chapa.create.phrase_service.get_random",
            return_value=mock_phrase,
        ):
            await handle_create_chapa.__wrapped__.__wrapped__(update, MagicMock())
            # Calls reply_text with error then usage
            assert update.effective_message.reply_text.call_count == 2
            assert (
                "La hora me la das con puntos"
                in update.effective_message.reply_text.call_args_list[0][0][0]
            )

    @pytest.mark.asyncio
    async def test_handle_create_chapa_bad_hour(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 2500"
        update.effective_message.reply_text = AsyncMock()

        mock_phrase = Phrase(text="cuñao")
        with patch(
            "tg.handlers.chapa.create.phrase_service.get_random",
            return_value=mock_phrase,
        ):
            await handle_create_chapa.__wrapped__.__wrapped__(update, MagicMock())
            assert (
                "Mal valor de horas"
                in update.effective_message.reply_text.call_args_list[0][0][0]
            )

    @pytest.mark.asyncio
    async def test_handle_create_chapa_bad_minute(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1099"
        update.effective_message.reply_text = AsyncMock()

        mock_phrase = Phrase(text="cuñao")
        with patch(
            "tg.handlers.chapa.create.phrase_service.get_random",
            return_value=mock_phrase,
        ):
            await handle_create_chapa.__wrapped__.__wrapped__(update, MagicMock())
            assert (
                "Mal valor de minutos"
                in update.effective_message.reply_text.call_args_list[0][0][0]
            )

    @pytest.mark.asyncio
    async def test_handle_create_chapa_bad_query(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1000 ??"
        update.effective_message.reply_text = AsyncMock()

        mock_phrase = Phrase(text="cuñao")
        with patch(
            "tg.handlers.chapa.create.phrase_service.get_random",
            return_value=mock_phrase,
        ):
            await handle_create_chapa.__wrapped__.__wrapped__(update, MagicMock())
            assert (
                "No entiendo esos parametros"
                in update.effective_message.reply_text.call_args_list[0][0][0]
            )

    @pytest.mark.asyncio
    async def test_handle_create_chapa_no_chat(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 frase"
        update.effective_chat = None

        with patch("services.schedule_repo.save") as mock_save:
            await handle_create_chapa.__wrapped__.__wrapped__(update, MagicMock())
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_create_chapa_success(self):
        update = MagicMock()
        update.effective_message.text = "/chapa 1030 frase"
        update.effective_message.reply_text = AsyncMock()
        update.effective_chat.id = 123
        update.effective_user.id = 456
        update.effective_chat.type = Chat.PRIVATE

        with patch("services.schedule_repo.save") as mock_save:
            await handle_create_chapa.__wrapped__.__wrapped__(update, MagicMock())
            mock_save.assert_called_once()
            schedule = mock_save.call_args[0][0]
            assert schedule.hour == 10
            assert schedule.minute == 30
            assert schedule.query == "frase"

    @pytest.mark.asyncio
    async def test_handle_list_chapas_no_chat(self):
        update = MagicMock()
        update.effective_chat = None
        await handle_list_chapas.__wrapped__(update, MagicMock())

    @pytest.mark.asyncio
    async def test_handle_list_chapas_no_tasks(self):
        update = MagicMock()
        update.effective_chat.id = 456
        update.effective_message.reply_text = AsyncMock()
        mock_phrase = Phrase(text="cuñao")
        with (
            patch("services.schedule_repo.get_schedules", return_value=[]),
            patch(
                "tg.handlers.chapa.list.phrase_service.get_random",
                return_value=mock_phrase,
            ),
        ):
            await handle_list_chapas.__wrapped__(update, MagicMock())
            update.effective_message.reply_text.assert_called_once()
            assert (
                "No hay ninguna chapa"
                in update.effective_message.reply_text.call_args[0][0]
            )

    @pytest.mark.asyncio
    async def test_handle_list_chapas_success(self):
        update = MagicMock()
        update.effective_chat.id = 456
        update.effective_message.reply_text = AsyncMock()

        mock_task = MagicMock()
        mock_task.hour = 10
        mock_task.minute = 30
        mock_task.query = "test"

        with patch("services.schedule_repo.get_schedules", return_value=[mock_task]):
            await handle_list_chapas.__wrapped__(update, MagicMock())
            update.effective_message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_no_chat(self):
        update = MagicMock()
        update.effective_chat = None
        await handle_delete_chapa.__wrapped__.__wrapped__(update, MagicMock())
        # Should return early

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_no_tasks(self):
        update = MagicMock()
        update.effective_chat.id = 456
        update.effective_message.reply_text = AsyncMock()

        mock_phrase = Phrase(text="cuñao")
        with (
            patch("services.schedule_repo.get_schedules", return_value=[]),
            patch(
                "tg.handlers.chapa.delete.phrase_service.get_random",
                return_value=mock_phrase,
            ),
        ):
            await handle_delete_chapa.__wrapped__.__wrapped__(update, MagicMock())
            update.effective_message.reply_text.assert_called_once()
            assert (
                "No hay ninguna chapa"
                in update.effective_message.reply_text.call_args[0][0]
            )

    @pytest.mark.asyncio
    async def test_handle_delete_chapa_success(self):
        update = MagicMock()
        update.effective_chat.id = 456
        update.effective_message.reply_text = AsyncMock()

        mock_task = MagicMock()
        mock_task.id = "123"

        with (
            patch("services.schedule_repo.get_schedules", return_value=[mock_task]),
            patch("services.schedule_repo.delete") as mock_delete,
        ):
            await handle_delete_chapa.__wrapped__.__wrapped__(update, MagicMock())
            mock_delete.assert_called_once_with("123")
