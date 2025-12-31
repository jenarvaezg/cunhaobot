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
    async def test_handle_callback_query_not_admin(self):
        update = MagicMock()
        update.callback_query.data = "LIKE:123:Proposal"
        update.callback_query.from_user.id = 999
        update.callback_query.answer = AsyncMock()

        context = MagicMock()
        admin = MagicMock()
        admin.user.id = 1
        context.bot.get_chat_administrators = AsyncMock(return_value=[admin])

        with (
            patch(
                "tg.handlers.utils.callback_query.phrase_service.get_random"
            ) as mock_random,
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            mock_random.return_value.text = "cuñao"
            await handle_callback_query(update, context)
            update.callback_query.answer.assert_called_with(
                "Tener una silla en el consejo no te hace maestro cuñao, cuñao"
            )

    @pytest.mark.asyncio
    async def test_handle_callback_query_proposal_not_found(self):
        update = MagicMock()
        update.callback_query.data = "LIKE:123:Proposal"
        update.callback_query.from_user.id = 1
        update.callback_query.answer = AsyncMock()

        context = MagicMock()
        admin = MagicMock()
        admin.user.id = 1
        cb_query.admins = [admin]

        with (
            patch("services.proposal_repo.load", return_value=None),
            patch(
                "tg.handlers.utils.callback_query.phrase_service.get_random"
            ) as mock_random,
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            mock_random.return_value.text = "cuñao"
            await handle_callback_query(update, context)
            update.callback_query.answer.assert_called_with(
                "Esa propuesta ha muerto, cuñao"
            )

    @pytest.mark.asyncio
    async def test_handle_callback_query_vote_and_approve(self):
        update = MagicMock()
        update.callback_query.data = "LIKE:123:Proposal"
        update.callback_query.from_user.id = 1
        update.callback_query.answer = AsyncMock()

        context = MagicMock()
        admin = MagicMock()
        admin.user.id = 1
        admin.user.name = "Admin"
        cb_query.admins = [admin]  # 1 admin -> 1 vote required

        p = Proposal(id="123", text="test", from_chat_id=1)

        with (
            patch("services.proposal_repo.load", return_value=p),
            patch(
                "tg.handlers.utils.callback_query.proposal_service.vote"
            ) as mock_vote,
            patch(
                "tg.handlers.utils.callback_query.approve_proposal",
                new_callable=AsyncMock,
            ) as mock_approve,
            patch("tg.decorators.user_service.update_or_create_user"),
        ):
            # Mock vote behavior (manually add to p since we mock the service)
            def side_effect(prop, user_id, pos):
                prop.liked_by.append(str(user_id))

            mock_vote.side_effect = side_effect

            await handle_callback_query(update, context)

            mock_vote.assert_called_once()
            mock_approve.assert_called_once_with(p, context.bot, update.callback_query)

    @pytest.mark.asyncio
    async def test_handle_callback_query_vote_and_dismiss(self):
        update = MagicMock()
        update.callback_query.data = "DISLIKE:123:LongProposal"
        update.callback_query.from_user.id = 1
        update.callback_query.answer = AsyncMock()

        context = MagicMock()
        admin = MagicMock()
        admin.user.id = 1
        cb_query.admins = [admin]

        p = LongProposal(id="123", text="test")

        with (
            patch("services.long_proposal_repo.load", return_value=p),
            patch(
                "tg.handlers.utils.callback_query.proposal_service.vote"
            ) as mock_vote,
            patch(
                "tg.handlers.utils.callback_query.dismiss_proposal",
                new_callable=AsyncMock,
            ) as mock_dismiss,
            patch("tg.decorators.user_service.update_or_create_user"),
        ):

            def side_effect(prop, user_id, pos):
                prop.disliked_by.append(str(user_id))

            mock_vote.side_effect = side_effect

            await handle_callback_query(update, context)
            mock_dismiss.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_proposal_web(self):
        p = Proposal(id="123", text="test", from_chat_id=123)
        bot = MagicMock()
        bot.send_message = AsyncMock()

        cb_query.admins = []

        with (
            patch(
                "tg.handlers.utils.callback_query._ensure_admins",
                new_callable=AsyncMock,
            ),
            patch("services.proposal_repo.save"),
            patch("tg.handlers.utils.callback_query.phrase_service") as mock_ph_svc,
            patch(
                "tg.handlers.utils.callback_query.get_vote_summary",
                return_value="summary",
            ),
        ):
            mock_ph_svc.get_random.return_value.text = "cuñao"
            mock_ph_svc.create_from_proposal = AsyncMock()

            await approve_proposal(p, bot)

            # Should send 2 messages: one to mod chat, one to proposer
            assert bot.send_message.call_count == 2
            mock_ph_svc.create_from_proposal.assert_called_once_with(p, bot)

    @pytest.mark.asyncio
    async def test_dismiss_proposal_web(self):
        p = Proposal(id="123", text="test", from_chat_id=123)
        bot = MagicMock()
        bot.send_message = AsyncMock()

        with (
            patch(
                "tg.handlers.utils.callback_query._ensure_admins",
                new_callable=AsyncMock,
            ),
            patch("services.proposal_repo.save"),
            patch("services.proposal_repo.delete") as mock_delete,
            patch("tg.handlers.utils.callback_query.phrase_service") as mock_ph_svc,
            patch(
                "tg.handlers.utils.callback_query.get_vote_summary",
                return_value="summary",
            ),
        ):
            mock_ph_svc.get_random.return_value.text = "cuñao"

            await dismiss_proposal(p, bot)

            assert bot.send_message.call_count == 2
            mock_delete.assert_called_once_with("123")

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
    async def test_approve_proposal_errors(self):
        p = Proposal(id="123", text="test", from_chat_id=123)
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=Exception("Fail"))

        with (
            patch(
                "tg.handlers.utils.callback_query._ensure_admins",
                new_callable=AsyncMock,
            ),
            patch("services.proposal_repo.save"),
            patch("tg.handlers.utils.callback_query.phrase_service") as mock_ph_svc,
            patch(
                "tg.handlers.utils.callback_query.get_vote_summary",
                return_value="summary",
            ),
        ):
            mock_ph_svc.get_random.return_value.text = "cuñao"
            mock_ph_svc.create_from_proposal = AsyncMock()

            # Should not raise exception
            await approve_proposal(p, bot)
            assert bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_dismiss_proposal_errors(self):
        p = Proposal(id="123", text="test", from_chat_id=123)
        bot = MagicMock()
        bot.send_message = AsyncMock(side_effect=Exception("Fail"))

        with (
            patch(
                "tg.handlers.utils.callback_query._ensure_admins",
                new_callable=AsyncMock,
            ),
            patch("services.proposal_repo.save"),
            patch("services.proposal_repo.delete"),
            patch("tg.handlers.utils.callback_query.phrase_service") as mock_ph_svc,
            patch(
                "tg.handlers.utils.callback_query.get_vote_summary",
                return_value="summary",
            ),
        ):
            mock_ph_svc.get_random.return_value.text = "cuñao"

            # Should not raise exception
            await dismiss_proposal(p, bot)
            assert bot.send_message.call_count == 2
