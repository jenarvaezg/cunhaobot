import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tg.handlers.messages.reply import handle_reply
from models.phrase import Phrase, LongPhrase


@pytest.mark.asyncio
async def test_handle_reply_not_to_me():
    update = MagicMock()
    update.effective_message.reply_to_message.from_user.username = "other"
    context = MagicMock()
    context.bot.username = "me"

    with patch(
        "tg.handlers.messages.reply.handle_message", new_callable=AsyncMock
    ) as mock_handle:
        await handle_reply(update, context)
        mock_handle.assert_called_once()


@pytest.mark.asyncio
async def test_handle_reply_to_me_phrase_prompt():
    update = MagicMock()
    update.effective_message.text = "New phrase"
    update.effective_message.reply_to_message.from_user.username = "me"
    update.effective_message.reply_to_message.text = (
        f"¿Qué {Phrase.display_name} quieres proponer?"
    )

    context = MagicMock()
    context.bot.username = "me"

    with patch(
        "tg.handlers.commands.submit.submit_handling", new_callable=AsyncMock
    ) as mock_submit:
        await handle_reply(update, context)
        mock_submit.assert_called_once_with(
            context.bot, update, is_long=False, text="New phrase"
        )


@pytest.mark.asyncio
async def test_handle_reply_to_me_long_phrase_prompt():
    update = MagicMock()
    update.effective_message.text = "New long phrase"
    update.effective_message.reply_to_message.from_user.username = "me"
    update.effective_message.reply_to_message.text = (
        f"¿Qué {LongPhrase.display_name} quieres proponer?"
    )

    context = MagicMock()
    context.bot.username = "me"

    with patch(
        "tg.handlers.commands.submit.submit_handling", new_callable=AsyncMock
    ) as mock_submit:
        await handle_reply(update, context)
        mock_submit.assert_called_once_with(
            context.bot, update, is_long=True, text="New long phrase"
        )


@pytest.mark.asyncio
async def test_handle_reply_no_message():
    update = MagicMock()
    update.effective_message = None
    assert await handle_reply(update, MagicMock()) is None
