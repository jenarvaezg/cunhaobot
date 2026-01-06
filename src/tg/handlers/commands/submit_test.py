import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.submit import (
    handle_submit,
    submit_handling,
)
from models.phrase import Phrase
from models.proposal import Proposal


@pytest.fixture
def mock_services():
    with patch("tg.handlers.commands.submit.services") as ms:
        ms.phrase_service.get_random = AsyncMock()
        ms.phrase_service.get_random.return_value.text = "cuñao"
        ms.phrase_service.find_most_similar = AsyncMock()
        ms.proposal_service.find_most_similar_proposal = AsyncMock(
            return_value=(None, 0)
        )
        ms.usage_service.log_usage = AsyncMock(return_value=[])
        ms.user_service.update_or_create_user = AsyncMock()
        ms.proposal_repo.save = AsyncMock()
        ms.long_proposal_repo.save = AsyncMock()
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
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    mock_services.phrase_service.find_most_similar.return_value = (
        Phrase(text="sim"),
        50,
    )
    mock_services.proposal_service.find_most_similar_proposal.return_value = (None, 0)

    context = MagicMock()
    context.bot.send_message = AsyncMock()

    with patch("tg.handlers.commands.submit.config") as mock_config:
        mock_config.mod_chat_id = 123
        await handle_submit(update, context)

    mock_services.proposal_repo.save.assert_called_once_with(mock_proposal)
    update.effective_message.reply_text.assert_called_once()
    assert (
        "Tu aportación será valorada"
        in update.effective_message.reply_text.call_args[0][0]
    )


@pytest.mark.asyncio
async def test_handle_submit_duplicate_phrase(mock_services):
    update = MagicMock()
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    # Similarity > 90
    mock_services.phrase_service.find_most_similar.return_value = (
        Phrase(text="test"),
        95,
    )

    context = MagicMock()
    await handle_submit(update, context)

    mock_services.proposal_repo.save.assert_not_called()
    msg = update.effective_message.reply_text.call_args[0][0]
    assert "Esa ya la tengo aprobada" in msg
    assert "Se parece demasiado" in msg


@pytest.mark.asyncio
async def test_handle_submit_duplicate_proposal_voting_active(mock_services):
    update = MagicMock()
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    mock_services.phrase_service.find_most_similar.return_value = (
        Phrase(text="sim"),
        50,
    )

    # Similar proposal, voting active
    existing_proposal = Proposal(text="test", id="2", voting_ended=False)
    mock_services.proposal_service.find_most_similar_proposal.return_value = (
        existing_proposal,
        95,
    )

    context = MagicMock()
    await handle_submit(update, context)

    mock_services.proposal_repo.save.assert_not_called()
    msg = update.effective_message.reply_text.call_args[0][0]
    assert "está siendo votada ahora mismo" in msg


@pytest.mark.asyncio
async def test_handle_submit_duplicate_proposal_rejected(mock_services):
    update = MagicMock()
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal
    mock_services.phrase_service.find_most_similar.return_value = (
        Phrase(text="sim"),
        50,
    )

    # Similar proposal, voting ended
    existing_proposal = Proposal(text="test", id="2", voting_ended=True)
    mock_services.proposal_service.find_most_similar_proposal.return_value = (
        existing_proposal,
        95,
    )

    context = MagicMock()
    await handle_submit(update, context)

    mock_services.proposal_repo.save.assert_not_called()
    msg = update.effective_message.reply_text.call_args[0][0]
    assert "fue rechazada" in msg


@pytest.mark.asyncio
async def test_handle_submit_too_long(mock_services):
    update = MagicMock()
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.text = "/proponer one two three four five six"
    update.effective_message.reply_text = AsyncMock()

    context = MagicMock()
    await handle_submit(update, context)

    mock_services.proposal_repo.save.assert_not_called()
    update.effective_message.reply_text.assert_called_once()
    assert (
        "Mejor prueba con /proponerfrase"
        in update.effective_message.reply_text.call_args[0][0]
    )


@pytest.mark.asyncio
async def test_handle_submit_empty(mock_services):
    update = MagicMock()
    update.effective_user.username = "testuser"
    update.effective_chat.type = "private"
    update.effective_chat.title = "Chat"
    update.effective_message.text = "/proponer"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="", id="1")
    mock_services.proposal_service.create_from_update.return_value = mock_proposal

    context = MagicMock()

    await handle_submit(update, context)

    mock_services.proposal_repo.save.assert_not_called()
    update.effective_message.reply_text.assert_called_once()
    assert "quieres proponer" in update.effective_message.reply_text.call_args[0][0]
