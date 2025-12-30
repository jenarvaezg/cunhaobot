import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tg.handlers.commands.submit import (
    handle_submit,
    handle_submit_phrase,
    _notify_proposal_to_curators,
    submit_handling,
)
from models.phrase import Phrase, LongPhrase
from models.proposal import Proposal, LongProposal


@pytest.fixture
def mock_deps():
    with (
        patch("tg.handlers.commands.submit.proposal_service") as ps,
        patch("tg.handlers.commands.submit.phrase_service") as phs,
        patch("tg.handlers.commands.submit.proposal_repo") as pr,
        patch("tg.handlers.commands.submit.long_proposal_repo") as lpr,
        patch("tg.decorators.user_service.update_or_create_user"),
        patch("tg.handlers.commands.submit.config") as config,
    ):
        phs.get_random.return_value.text = "cuñao"
        config.mod_chat_id = 123
        yield ps, phs, pr, lpr


@pytest.mark.asyncio
async def test_submit_handling_no_user(mock_deps):
    ps, phs, pr, lpr = mock_deps
    bot = MagicMock()
    update = MagicMock()
    update.effective_user = None
    update.effective_message = MagicMock()

    result = await submit_handling(bot, update, is_long=False)
    assert result is None

    ps.create_from_update.assert_not_called()


@pytest.mark.asyncio
async def test_handle_submit_success(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_user.name = "test_user"
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    ps.create_from_update.return_value = mock_proposal
    phs.find_most_similar.return_value = (Phrase(text="sim"), 50)

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


@pytest.mark.asyncio
async def test_handle_submit_duplicate(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    ps.create_from_update.return_value = mock_proposal
    phs.find_most_similar.return_value = (Phrase(text="test"), 100)

    context = MagicMock()
    await handle_submit(update, context)

    pr.save.assert_not_called()
    update.effective_message.reply_text.assert_called_once()
    assert "Esa ya la tengo" in update.effective_message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_submit_similar(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_message.text = "/proponer test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = Proposal(text="test", id="1")
    ps.create_from_update.return_value = mock_proposal
    phs.find_most_similar.return_value = (Phrase(text="sim"), 95)

    context = MagicMock()
    await handle_submit(update, context)

    pr.save.assert_not_called()
    update.effective_message.reply_text.assert_called_once()
    assert "Se parece demasiado" in update.effective_message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_handle_submit_phrase_success(mock_deps):
    ps, phs, pr, lpr = mock_deps
    update = MagicMock()
    update.effective_user.name = "test_user"
    update.effective_message.text = "/proponerfrase long test"
    update.effective_message.reply_text = AsyncMock()

    mock_proposal = LongProposal(text="long test", id="1")
    ps.create_from_update.return_value = mock_proposal
    phs.find_most_similar.return_value = (LongPhrase(text="sim"), 50)

    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await handle_submit_phrase(update, context)

    lpr.save.assert_called_once_with(mock_proposal)
    update.effective_message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_notify_curators(mock_deps):
    ps, phs, pr, lpr = mock_deps
    bot = AsyncMock()
    proposal = Proposal(text="test", id="1")
    similar = Phrase(text="sim")

    await _notify_proposal_to_curators(bot, proposal, "User", similar, 50)

    bot.send_message.assert_called_once()
    args = bot.send_message.call_args
    assert args[0][0] == 123  # mod_chat_id
    assert "test" in args[0][1]
    assert "sim" in args[0][1]
