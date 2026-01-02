import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.submit import (
    handle_submit,
    submit_handling,
)
from models.phrase import Phrase
from models.proposal import Proposal


@pytest.fixture
def mock_deps():
    with (
        patch("tg.handlers.commands.submit.proposal_service") as ps,
        patch("tg.handlers.commands.submit.phrase_service") as phs,
        patch("tg.handlers.commands.submit.proposal_repo") as pr,
        patch("tg.handlers.commands.submit.long_proposal_repo") as lpr,
        patch("tg.decorators.user_service.update_or_create_user"),
        patch("tg.handlers.commands.submit.usage_service") as us,
        patch("tg.handlers.commands.submit.notify_new_badges") as nnb,
        patch("tg.handlers.commands.submit.config") as config,
    ):
        phs.get_random.return_value.text = "cuñao"
        ps.find_most_similar_proposal.return_value = (None, 0)
        config.mod_chat_id = 123
        us.log_usage = AsyncMock(return_value=[])
        nnb.return_value = AsyncMock()
        yield ps, phs, pr, lpr


@pytest.mark.asyncio
async def test_submit_handling_no_user(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_user = None
    update.effective_message = MagicMock()
    context = MagicMock()

    result = await submit_handling(update, context, is_long=False)
    assert result is None
    ps.create_from_update.assert_not_called()


@pytest.mark.asyncio
async def test_handle_submit_success(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_user.name = "test_user"
    update.effective_user.id = 123
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    ps.create_from_update.return_value = mock_proposal
    phs.find_most_similar.return_value = (Phrase(text="sim"), 50)
    ps.find_most_similar_proposal.return_value = (None, 0)

    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await handle_submit(update, context)

    pr.save.assert_called_once_with(mock_proposal)
    update.effective_message.reply_text.assert_called_once()
    assert (
        "Tu aportación será valorada"
        in update.effective_message.reply_text.call_args[0][0]
    )


@pytest.mark.asyncio
async def test_handle_submit_duplicate_phrase(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    ps.create_from_update.return_value = mock_proposal
    # Similarity > 90
    phs.find_most_similar.return_value = (Phrase(text="test"), 95)

    context = MagicMock()
    await handle_submit(update, context)

    pr.save.assert_not_called()
    msg = update.effective_message.reply_text.call_args[0][0]
    assert "Esa ya la tengo aprobada" in msg
    assert "Se parece demasiado" in msg


@pytest.mark.asyncio
async def test_handle_submit_duplicate_proposal_voting_active(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    ps.create_from_update.return_value = mock_proposal
    phs.find_most_similar.return_value = (Phrase(text="sim"), 50)  # Not similar phrase

    # Similar proposal, voting active
    existing_proposal = Proposal(text="test", id="2", voting_ended=False)
    ps.find_most_similar_proposal.return_value = (existing_proposal, 95)

    context = MagicMock()
    await handle_submit(update, context)

    pr.save.assert_not_called()
    msg = update.effective_message.reply_text.call_args[0][0]
    assert "está siendo votada ahora mismo" in msg


@pytest.mark.asyncio
async def test_handle_submit_duplicate_proposal_rejected(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    ps.create_from_update.return_value = mock_proposal
    phs.find_most_similar.return_value = (Phrase(text="sim"), 50)

    # Similar proposal, voting ended (rejected, because if it was approved, phrase check would have caught it likely,
    # OR user explicit requirement says "Si existe y no la frase y la votacion acabo -> rechazado")
    existing_proposal = Proposal(text="test", id="2", voting_ended=True)
    ps.find_most_similar_proposal.return_value = (existing_proposal, 95)

    context = MagicMock()
    await handle_submit(update, context)

    pr.save.assert_not_called()
    msg = update.effective_message.reply_text.call_args[0][0]
    assert "fue rechazada" in msg


@pytest.mark.asyncio
async def test_handle_submit_too_long(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_message.text = "/proponer one two three four five six"
    update.effective_message.reply_text = AsyncMock()

    context = MagicMock()
    await handle_submit(update, context)

    pr.save.assert_not_called()
    update.effective_message.reply_text.assert_called_once()
    assert (
        "Mejor prueba con /proponerfrase"
        in update.effective_message.reply_text.call_args[0][0]
    )


@pytest.mark.asyncio
async def test_handle_submit_empty(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_message.text = "/proponer"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="", id="1")
    ps.create_from_update.return_value = mock_proposal

    context = MagicMock()

    await handle_submit(update, context)

    pr.save.assert_not_called()
    update.effective_message.reply_text.assert_called_once()
    assert "quieres proponer" in update.effective_message.reply_text.call_args[0][0]
