from models.phrase import Phrase  # Import the Phrase model
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.about import handle_about
from services.user_service import UserService  # Import the class


@pytest.mark.asyncio
async def test_handle_about():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    update.effective_message.chat.title = "Test Chat"  # Provide a string value
    update.effective_message.chat.PRIVATE = False  # is_group will be False
    update.effective_user.id = 12345
    update.effective_user.name = "Test User"  # Provide a string value
    update.effective_message.chat_id = 1
    context = MagicMock()

    mock_phrase = Phrase(text="cuñao")
    with (
        patch.object(
            UserService, "update_or_create_user"
        ),  # Patch the method on the class
        patch(
            "tg.handlers.commands.about.usage_service.log_usage",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "tg.handlers.commands.about.phrase_service.get_random",
            return_value=mock_phrase,
        ),
    ):
        await handle_about(update, context)
        update.effective_message.reply_text.assert_called_once()
