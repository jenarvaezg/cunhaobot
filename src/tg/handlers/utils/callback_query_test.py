import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tg.handlers.utils.callback_query import (
    handle_callback_query,
    approve_proposal,
    dismiss_proposal,
    _ensure_admins,
)
from tg.handlers.utils import callback_query as cb_query
from models.proposal import Proposal, LongProposal


@pytest.fixture(autouse=True)
def clear_admins():
    cb_query.admins = []
    yield
    cb_query.admins = []


class TestCallbackQuery:
    @pytest.mark.asyncio
    async def test_ensure_admins_success(self):
        bot = MagicMock()
        admin = MagicMock()
        bot.get_chat_administrators = AsyncMock(return_value=[admin])

        await _ensure_admins(bot)
        assert cb_query.admins == [admin]

    @pytest.mark.asyncio
    async def test_handle_callback_query_not_admin(self, mock_container):
        update = MagicMock()
        update.effective_user.username = "testuser"
        update.effective_chat.type = "private"
        update.effective_chat.title = "Chat"
        update.callback_query.data = "LIKE:123:Proposal"
        update.callback_query.from_user.id = 999
        update.callback_query.from_user.username = "testuser"
        update.callback_query.answer = AsyncMock()

        context = MagicMock()
        admin = MagicMock()
        admin.user.id = 1
        context.bot.get_chat_administrators = AsyncMock(return_value=[admin])

        mock_container["phrase_service"].get_random.return_value.text = "cuñao"

        await handle_callback_query(update, context)
        update.callback_query.answer.assert_called_with(
            "Tener una silla en el consejo no te hace maestro cuñao, cuñao"
        )

    @pytest.mark.asyncio
    async def test_handle_callback_query_proposal_not_found(self, mock_container):
        update = MagicMock()
        update.effective_user.username = "testuser"
        update.effective_chat.type = "private"
        update.effective_chat.title = "Chat"
        update.callback_query.data = "LIKE:123:Proposal"
        update.callback_query.from_user.id = 1
        update.callback_query.from_user.username = "testuser"
        update.callback_query.answer = AsyncMock()

        context = MagicMock()
        admin = MagicMock()
        admin.user.id = 1
        cb_query.admins = [admin]

        mock_container["proposal_repo"].load = AsyncMock(return_value=None)
        mock_container["phrase_service"].get_random.return_value.text = "cuñao"

        await handle_callback_query(update, context)
        update.callback_query.answer.assert_called_with(
            "Esa propuesta ha muerto, cuñao"
        )

    @pytest.mark.asyncio
    async def test_handle_callback_query_vote_and_approve(self, mock_container):
        update = MagicMock()
        update.effective_user.username = "testuser"
        update.effective_chat.type = "private"
        update.effective_chat.title = "Chat"
        update.callback_query.data = "LIKE:123:Proposal"
        update.callback_query.from_user.id = 1
        update.callback_query.from_user.username = "testuser"
        update.callback_query.answer = AsyncMock()

        context = MagicMock()
        admin = MagicMock()
        admin.user.id = 1
        admin.user.name = "Admin"
        cb_query.admins = [admin]

        p = Proposal(id="123", text="test", from_chat_id=1)

        mock_container["proposal_repo"].load = AsyncMock(return_value=p)
        # Mock save as well since it might be called
        mock_container["proposal_repo"].save = AsyncMock()

        with (
            patch(
                "tg.handlers.utils.callback_query.approve_proposal",
                new_callable=AsyncMock,
            ) as mock_approve,
            patch(
                "tg.handlers.utils.callback_query.get_required_votes",
                return_value=1,
            ),
        ):

            async def side_effect(prop, user_id, pos):
                prop.liked_by.append(str(user_id))

            mock_container["proposal_service"].vote.side_effect = side_effect

            await handle_callback_query(update, context)

            mock_container["proposal_service"].vote.assert_called_once()
            mock_approve.assert_called_once_with(p, context.bot, update.callback_query)

    @pytest.mark.asyncio
    async def test_handle_callback_query_vote_and_dismiss(self, mock_container):
        update = MagicMock()
        update.effective_user.username = "testuser"
        update.effective_chat.type = "private"
        update.effective_chat.title = "Chat"
        update.callback_query.data = "DISLIKE:123:LongProposal"
        update.callback_query.from_user.id = 1
        update.callback_query.from_user.username = "testuser"
        update.callback_query.answer = AsyncMock()

        context = MagicMock()
        admin = MagicMock()
        admin.user.id = 1
        cb_query.admins = [admin]

        p = LongProposal(id="123", text="test")

        mock_container["long_proposal_repo"].load = AsyncMock(return_value=p)
        mock_container["long_proposal_repo"].save = AsyncMock()

        with (
            patch(
                "tg.handlers.utils.callback_query.dismiss_proposal",
                new_callable=AsyncMock,
            ) as mock_dismiss,
            patch(
                "tg.handlers.utils.callback_query.get_required_votes",
                return_value=1,
            ),
        ):

            async def side_effect(prop, user_id, pos):
                prop.disliked_by.append(str(user_id))

            mock_container["proposal_service"].vote.side_effect = side_effect

            await handle_callback_query(update, context)
            mock_dismiss.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_proposal_web(self, mock_container):
        p = Proposal(id="123", text="test", from_chat_id=123)
        bot = MagicMock()
        bot.send_message = AsyncMock()

        cb_query.admins = []

        mock_container["phrase_service"].get_random.return_value.text = "cuñao"
        mock_container["usage_service"].log_usage.return_value = []
        mock_container["proposal_repo"].save = AsyncMock()
        mock_container["long_proposal_repo"].save = AsyncMock()

        with (
            patch(
                "tg.handlers.utils.callback_query._ensure_admins",
                new_callable=AsyncMock,
            ),
            patch(
                "tg.handlers.utils.callback_query.get_vote_summary",
                return_value="summary",
            ),
        ):
            await approve_proposal(p, bot)

            assert bot.send_message.call_count == 2
            mock_container[
                "phrase_service"
            ].create_from_proposal.assert_called_once_with(p, bot)

    @pytest.mark.asyncio
    async def test_dismiss_proposal_web(self, mock_container):
        p = Proposal(id="123", text="test", from_chat_id=123)
        bot = MagicMock()
        bot.send_message = AsyncMock()

        mock_container["phrase_service"].get_random.return_value.text = "cuñao"
        mock_container["usage_service"].log_usage.return_value = []
        mock_container["proposal_repo"].save = AsyncMock()
        mock_container["long_proposal_repo"].save = AsyncMock()

        with (
            patch(
                "tg.handlers.utils.callback_query._ensure_admins",
                new_callable=AsyncMock,
            ),
            patch(
                "tg.handlers.utils.callback_query.get_vote_summary",
                return_value="summary",
            ),
        ):
            await dismiss_proposal(p, bot)

            assert bot.send_message.call_count == 2
            assert p.voting_ended is True
            mock_container["proposal_repo"].save.assert_called_once_with(p)

    @pytest.mark.asyncio
    async def test_update_proposal_text_equal(self):
        from tg.handlers.utils.callback_query import _update_proposal_text

        p = Proposal(id="123", text="test", liked_by=["1"])
        callback_query = MagicMock()
        callback_query.message.text_markdown = "Original text\n\n*Han votado ya:*\nNew"
        callback_query.edit_message_text = AsyncMock()

        admin = MagicMock()
        admin.user.id = 1
        admin.user.name = "New"
        cb_query.admins = [admin]

        await _update_proposal_text(p, callback_query)
        # Should NOT call edit_message_text because text is already same
        callback_query.edit_message_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_vote_summary_with_dislikers(self):
        from tg.handlers.utils.callback_query import get_vote_summary

        admin = MagicMock()
        admin.user.id = 1
        admin.user.name = "Admin"
        cb_query.admins = [admin]

        p = Proposal(text="test", disliked_by=["1"])
        summary = get_vote_summary(p)
        assert "Han votado que no: Admin" in summary

    @pytest.mark.asyncio
    async def test_ensure_admins_error(self):
        bot = MagicMock()
        bot.get_chat_administrators = AsyncMock(side_effect=Exception("Fail"))
        await _ensure_admins(bot)
        assert cb_query.admins == []

    @pytest.mark.asyncio
    async def test_approve_proposal_errors(self, mock_container):
        p = Proposal(id="123", text="test", from_chat_id=123)
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=Exception("Fail"))

        mock_container["phrase_service"].get_random.return_value.text = "cuñao"
        mock_container["usage_service"].log_usage.return_value = []
        mock_container["proposal_repo"].save = AsyncMock()
        mock_container["long_proposal_repo"].save = AsyncMock()

        with (
            patch(
                "tg.handlers.utils.callback_query._ensure_admins",
                new_callable=AsyncMock,
            ),
            patch(
                "tg.handlers.utils.callback_query.get_vote_summary",
                return_value="summary",
            ),
        ):
            await approve_proposal(p, bot)
            assert bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_dismiss_proposal_errors(self, mock_container):
        p = Proposal(id="123", text="test", from_chat_id=123)
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=Exception("Fail"))

        mock_container["phrase_service"].get_random.return_value.text = "cuñao"
        mock_container["usage_service"].log_usage.return_value = []
        mock_container["proposal_repo"].save = AsyncMock()
        mock_container["long_proposal_repo"].save = AsyncMock()

        with (
            patch(
                "tg.handlers.utils.callback_query._ensure_admins",
                new_callable=AsyncMock,
            ),
            patch(
                "tg.handlers.utils.callback_query.get_vote_summary",
                return_value="summary",
            ),
        ):
            await dismiss_proposal(p, bot)
            assert bot.send_message.call_count == 2
