import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from tg.handlers.utils.callback_query import (
    handle_callback_query,
    _approve_proposal,
    _dismiss_proposal,
    _update_proposal_text,
    get_vote_summary,
)
from models.proposal import Proposal
from tg.constants import LIKE


class TestCallbackQuery:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Mock Phrase.get_random_phrase
        self.patcher_phrase = patch("models.phrase.Phrase.get_random_phrase")
        self.mock_phrase = self.patcher_phrase.start()
        self.mock_phrase.return_value = "cuñao"

        yield
        self.patcher_phrase.stop()

    @pytest.mark.asyncio
    async def test_handle_callback_query_not_admin(self):
        update = MagicMock()
        update.callback_query.data = "LIKE:123:Proposal"
        update.callback_query.from_user.id = 999
        update.callback_query.answer = AsyncMock()
        context = MagicMock()

        admin_member = MagicMock()
        admin_member.user.id = 1
        context.bot.get_chat_administrators = AsyncMock(return_value=[admin_member])

        with (
            patch("tg.handlers.utils.callback_query.admins", []),
            patch("models.proposal.Proposal.load", return_value=MagicMock()),
        ):
            await handle_callback_query(update, context)

        update.callback_query.answer.assert_called()

    @pytest.mark.asyncio
    async def test_handle_callback_query_proposal_not_found(self):
        update = MagicMock()
        update.callback_query.data = "LIKE:123:Proposal"
        update.callback_query.from_user.id = 1
        update.callback_query.answer = AsyncMock()
        context = MagicMock()

        admin_member = MagicMock()
        admin_member.user.id = 1
        context.bot.get_chat_administrators = AsyncMock(return_value=[admin_member])

        with (
            patch("tg.handlers.utils.callback_query.admins", [admin_member]),
            patch("models.proposal.Proposal.load", return_value=None),
        ):
            await handle_callback_query(update, context)
            update.callback_query.answer.assert_called()

    @pytest.mark.asyncio
    async def test_handle_callback_query_approve(self):
        update = MagicMock()
        update.callback_query.data = f"{LIKE}:123:Proposal"
        update.callback_query.from_user.id = 1
        update.callback_query.answer = AsyncMock()
        context = MagicMock()

        admin_member = MagicMock()
        admin_member.user.id = 1

        mock_proposal = MagicMock(spec=Proposal)
        mock_proposal.liked_by = [1, 2, 3]
        mock_proposal.disliked_by = []
        mock_proposal.kind = "Proposal"

        with (
            patch("tg.handlers.utils.callback_query.admins", [admin_member]),
            patch("models.proposal.Proposal.load", return_value=mock_proposal),
            patch("tg.handlers.utils.callback_query._add_vote", new_callable=AsyncMock),
            patch(
                "tg.handlers.utils.callback_query.get_required_votes", return_value=1
            ),
            patch(
                "tg.handlers.utils.callback_query._approve_proposal",
                new_callable=AsyncMock,
            ) as mock_approve,
        ):
            await handle_callback_query(update, context)
            mock_approve.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_query_dismiss(self):
        update = MagicMock()
        update.callback_query.data = "DISLIKE:123:Proposal"
        update.callback_query.from_user.id = 1
        update.callback_query.answer = AsyncMock()
        context = MagicMock()

        admin_member = MagicMock()
        admin_member.user.id = 1

        mock_proposal = MagicMock(spec=Proposal)
        mock_proposal.liked_by = []
        mock_proposal.disliked_by = [1, 2, 3]
        mock_proposal.kind = "Proposal"

        with (
            patch("tg.handlers.utils.callback_query.admins", [admin_member]),
            patch("models.proposal.Proposal.load", return_value=mock_proposal),
            patch("tg.handlers.utils.callback_query._add_vote", new_callable=AsyncMock),
            patch(
                "tg.handlers.utils.callback_query.get_required_votes", return_value=1
            ),
            patch(
                "tg.handlers.utils.callback_query._dismiss_proposal",
                new_callable=AsyncMock,
            ) as mock_dismiss,
        ):
            await handle_callback_query(update, context)
            mock_dismiss.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_proposal(self):
        p = MagicMock(spec=Proposal)
        p.text = "test"
        p.from_chat_id = 123
        p.from_message_id = 456
        p.liked_by = []
        p.disliked_by = []
        p.phrase_class.upload_from_proposal = AsyncMock()

        cb = MagicMock()
        cb.edit_message_text = AsyncMock()
        bot = MagicMock()
        bot.send_message = AsyncMock()

        with patch("tg.handlers.utils.callback_query.admins", [MagicMock()]):
            await _approve_proposal(p, cb, bot)

        cb.edit_message_text.assert_called_once()
        bot.send_message.assert_called_once()
        p.phrase_class.upload_from_proposal.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_proposal_from_web(self):
        p = MagicMock(spec=Proposal)
        p.text = "test"
        p.from_chat_id = 123
        p.from_message_id = 456
        p.liked_by = []
        p.disliked_by = []
        p.phrase_class.upload_from_proposal = AsyncMock()

        bot = MagicMock()
        bot.send_message = AsyncMock()

        with patch("tg.handlers.utils.callback_query.admins", [MagicMock()]):
            await _approve_proposal(p, None, bot)

        assert bot.send_message.call_count == 2
        p.phrase_class.upload_from_proposal.assert_called_once()

    @pytest.mark.asyncio
    async def test_dismiss_proposal(self):
        p = MagicMock(spec=Proposal)
        p.text = "test"
        p.from_chat_id = 123
        p.from_message_id = 456
        p.liked_by = []
        p.disliked_by = []

        cb = MagicMock()
        cb.edit_message_text = AsyncMock()
        bot = MagicMock()
        bot.send_message = AsyncMock()

        with patch("tg.handlers.utils.callback_query.admins", [MagicMock()]):
            await _dismiss_proposal(p, cb, bot)

        cb.edit_message_text.assert_called_once()
        bot.send_message.assert_called_once()
        p.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_proposal_text(self):
        p = MagicMock(spec=Proposal)
        p.id = "123"
        p.kind = "Proposal"
        p.liked_by = [1]
        p.disliked_by = []

        cb = MagicMock()
        cb.message.text_markdown = "Original text"
        cb.edit_message_text = AsyncMock()

        mock_admin = MagicMock()
        mock_admin.user.id = 1
        mock_admin.user.name = "Admin1"

        with (
            patch("tg.handlers.utils.callback_query.admins", [mock_admin]),
            patch(
                "tg.handlers.utils.callback_query.build_vote_keyboard", return_value=[]
            ),
        ):
            await _update_proposal_text(p, cb)
            cb.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_query_vote(self):
        update = MagicMock()
        update.callback_query.data = f"{LIKE}:123:Proposal"
        update.callback_query.from_user.id = 1
        update.callback_query.answer = AsyncMock()
        context = MagicMock()

        admin_member = MagicMock()
        admin_member.user.id = 1

        mock_proposal = MagicMock(spec=Proposal)
        mock_proposal.liked_by = []
        mock_proposal.disliked_by = []
        mock_proposal.kind = "Proposal"

        with (
            patch("tg.handlers.utils.callback_query.admins", [admin_member]),
            patch("models.proposal.Proposal.load", return_value=mock_proposal),
            patch(
                "tg.handlers.utils.callback_query.get_required_votes", return_value=5
            ),
            patch(
                "tg.handlers.utils.callback_query._update_proposal_text",
                new_callable=AsyncMock,
            ),
        ):
            await handle_callback_query(update, context)

            mock_proposal.add_vote.assert_called()
            mock_proposal.save.assert_called()
            update.callback_query.answer.assert_called()

    @pytest.mark.asyncio
    async def test_handle_callback_query_no_data(self):
        update = MagicMock()
        update.callback_query.data = None
        context = MagicMock()
        context.bot.get_chat_administrators = AsyncMock()
        await handle_callback_query(update, context)

    def test_get_vote_summary(self):
        p = MagicMock()
        p.liked_by = [1]
        p.disliked_by = [2]

        mock_admin1 = MagicMock()
        mock_admin1.user.id = 1
        mock_admin1.user.name = "A1"
        mock_admin2 = MagicMock()
        mock_admin2.user.id = 2
        mock_admin2.user.name = "A2"

        # Use sys.modules to patch the actual module's global
        sys.modules["tg.handlers.utils.callback_query"].admins = [
            mock_admin1,
            mock_admin2,
        ]

        summary = get_vote_summary(p)
        assert "A1" in summary
        assert "A2" in summary
