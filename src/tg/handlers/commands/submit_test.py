import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.submit import (
    handle_submit,
    submit_handling,
)
from models.proposal import Proposal
from services.proposal_service import IntakeResult, IntakeStatus


@pytest.fixture
def mock_services():
    with patch("tg.handlers.commands.submit.services") as ms:
        ms.phrase_service.get_random = AsyncMock()
        ms.phrase_service.get_random.return_value.text = "cuñao"
        # The deepened intake module owns the decision; the handler only
        # translates the IntakeResult it returns.
        ms.proposal_service.submit = AsyncMock()
        ms.usage_service.log_usage = AsyncMock(return_value=[])
        ms.user_service.update_or_create_user = AsyncMock()
        yield ms


@pytest.mark.asyncio
async def test_submit_handling_no_user(mock_services):
    update = MagicMock()
    update.effective_user = None
    update.effective_message = MagicMock()
    context = MagicMock()

    result = await submit_handling(update, context, is_long=False)
    assert result is None
    mock_services.proposal_service.create_from_update.assert_not_called()


@pytest.mark.asyncio
async def test_handle_submit_success(mock_services):
    update = MagicMock()
    update.effective_user.name = "test_user"
    update.effective_user.username = "test_user"
    update.effective_user.id = 123
    update.effective_message.chat.type = "private"
    update.effective_message.chat.title = "Chat"
    update.effective_message.chat.username = "testchat"
    update.effective_message.chat_id = 123
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    mock_services.proposal_service.submit.return_value = IntakeResult(
        IntakeStatus.ACCEPTED, proposal=mock_proposal, similar_text="sim", similarity=50
    )

    context = MagicMock()
    context.bot.send_message = AsyncMock()

    with patch("tg.handlers.commands.submit.config") as mock_config:
        mock_config.mod_chat_id = 123
        await handle_submit(update, context)

    # Accepted proposals are forwarded to the Consejo and the proposer is thanked.
    context.bot.send_message.assert_called_once()
    assert (
        "Tu aportación será valorada"
        in update.effective_message.reply_text.call_args[0][0]
    )


@pytest.mark.asyncio
async def test_handle_submit_duplicate_phrase(mock_services):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "testuser"
    update.effective_message.chat.type = "private"
    update.effective_message.chat_id = 123
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    mock_services.proposal_service.submit.return_value = IntakeResult(
        IntakeStatus.DUPLICATE_APPROVED, similar_text="test", similarity=95
    )

    context = MagicMock()
    await handle_submit(update, context)

    msg = update.effective_message.reply_text.call_args[0][0]
    assert "Esa ya la tengo aprobada" in msg
    assert "Se parece demasiado" in msg


@pytest.mark.asyncio
async def test_handle_submit_duplicate_proposal_voting_active(mock_services):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "testuser"
    update.effective_message.chat.type = "private"
    update.effective_message.chat_id = 123
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    existing_proposal = Proposal(text="test", id="2", voting_ended=False)
    mock_services.proposal_service.submit.return_value = IntakeResult(
        IntakeStatus.DUPLICATE_ACTIVE, proposal=existing_proposal, similarity=95
    )

    context = MagicMock()
    await handle_submit(update, context)

    msg = update.effective_message.reply_text.call_args[0][0]
    assert "está siendo votada ahora mismo" in msg


@pytest.mark.asyncio
async def test_handle_submit_duplicate_proposal_rejected(mock_services):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "testuser"
    update.effective_message.chat.type = "private"
    update.effective_message.chat_id = 123
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    existing_proposal = Proposal(text="test", id="2", voting_ended=True)
    mock_services.proposal_service.submit.return_value = IntakeResult(
        IntakeStatus.DUPLICATE_REJECTED, proposal=existing_proposal, similarity=95
    )

    context = MagicMock()
    await handle_submit(update, context)

    msg = update.effective_message.reply_text.call_args[0][0]
    assert "fue rechazada" in msg


@pytest.mark.asyncio
async def test_handle_submit_too_long(mock_services):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "testuser"
    update.effective_message.chat.type = "private"
    update.effective_message.chat_id = 123
    update.effective_message.text = "/proponer one two three four five six"
    update.effective_message.reply_text = AsyncMock()

    context = MagicMock()
    await handle_submit(update, context)

    # Too-long short proposals are short-circuited before intake runs.
    mock_services.proposal_service.submit.assert_not_called()
    update.effective_message.reply_text.assert_called_once()
    assert (
        "Mejor prueba con /proponerfrase"
        in update.effective_message.reply_text.call_args[0][0]
    )


@pytest.mark.asyncio
async def test_handle_submit_empty(mock_services):
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.name = "Test"
    update.effective_user.username = "testuser"
    update.effective_message.chat.type = "private"
    update.effective_message.chat_id = 123
    update.effective_message.text = "/proponer"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    mock_services.proposal_service.submit.return_value = IntakeResult(
        IntakeStatus.EMPTY
    )

    context = MagicMock()
    await handle_submit(update, context)

    update.effective_message.reply_text.assert_called_once()
    assert "quieres proponer" in update.effective_message.reply_text.call_args[0][0]
