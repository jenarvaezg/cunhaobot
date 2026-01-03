import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from models.proposal import Proposal, LongProposal
from models.user import User
from services.proposal_service import ProposalService


class TestProposalService:
    @pytest.fixture
    def service(self):
        self.repo = AsyncMock()
        self.long_repo = AsyncMock()
        self.user_repo = AsyncMock()
        return ProposalService(self.repo, self.long_repo, self.user_repo)

    def test_create_from_update_validation(self, service):
        update = MagicMock()
        update.effective_message = None
        with pytest.raises(ValueError):
            service.create_from_update(update)

        update.effective_message = MagicMock()
        update.effective_user = None
        with pytest.raises(ValueError):
            service.create_from_update(update)

    def test_create_from_update_long(self, service):
        update = MagicMock()
        update.effective_message.chat.id = 1
        update.effective_message.message_id = 2
        update.effective_message.text = "long text"
        update.effective_user.id = 3

        p = service.create_from_update(update, is_long=True)
        assert isinstance(p, LongProposal)
        assert p.text == "long text"

    def test_create_from_update_with_text_override(self, service):
        update = MagicMock()
        update.effective_message.chat.id = 1
        update.effective_message.message_id = 2
        update.effective_user.id = 3

        p = service.create_from_update(update, text="override")
        assert p.text == "override"

    def test_create_from_update_reply(self, service):
        update = MagicMock()
        update.effective_message.text = "/proponer"
        update.effective_message.reply_to_message.text = "reply text"
        update.effective_user.id = 3

        p = service.create_from_update(update)
        assert p.text == "reply text"

    @pytest.mark.asyncio
    async def test_vote(self, service):
        p = Proposal(
            id="123", from_chat_id=456, from_message_id=789, text="test", user_id=10
        )
        with patch(
            "services.proposal_service.user_service", new_callable=AsyncMock
        ) as mock_user_service:
            await service.vote(p, voter_id=1, positive=True)
            assert p.liked_by == ["1"]
            self.repo.save.assert_called_once_with(p)
            # Proposer (id=10) gets 1 point
            mock_user_service.add_points.assert_called_once_with(10, 1)

    @pytest.mark.asyncio
    async def test_vote_long(self, service):
        p = LongProposal(
            id="123", from_chat_id=456, from_message_id=789, text="test", user_id=10
        )
        with patch(
            "services.proposal_service.user_service", new_callable=AsyncMock
        ) as mock_user_service:
            await service.vote(p, voter_id=1, positive=True)
            assert p.liked_by == ["1"]
            self.long_repo.save.assert_called_once_with(p)
            mock_user_service.add_points.assert_called_once_with(10, 1)

    @pytest.mark.asyncio
    async def test_vote_switch(self, service):
        p = Proposal(
            id="123", from_chat_id=456, from_message_id=789, text="test", liked_by=["1"]
        )
        with patch("services.proposal_service.user_service", new_callable=AsyncMock):
            await service.vote(p, voter_id=1, positive=False)
            assert p.liked_by == []
            assert p.disliked_by == ["1"]

    @pytest.mark.asyncio
    async def test_get_curators_cached(self, service):
        service._curators_cache = {"1": "User 1"}
        service._last_update = datetime.now()

        curators = await service.get_curators()
        assert curators == {"1": "User 1"}

    @pytest.mark.asyncio
    async def test_update_curators_cache(self, service):
        mock_bot = AsyncMock()
        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_app.initialize = AsyncMock()

        admin_user = MagicMock()
        admin_user.user.is_bot = False
        admin_user.user.id = 100
        admin_user.user.name = "Admin"

        mock_bot.get_chat_administrators.return_value = [admin_user]

        # Patch where it's imported or used.
        # Since it's imported inside the method, we must ensure `tg` module has the mock.
        with patch("tg.get_tg_application", return_value=mock_app):
            with patch("services.proposal_service.config") as mock_config:
                mock_config.mod_chat_id = 123

                # Setup proposals to find active users
                p1 = Proposal(
                    id="1",
                    from_chat_id=1,
                    from_message_id=1,
                    text="t",
                    user_id=200,
                    liked_by=["300"],
                )
                service.repo.load_all.return_value = [p1]
                service.long_repo.load_all.return_value = []

                # Setup user repos
                u1 = User(id=200, name="User 200")
                service.user_repo.load_all.return_value = [u1]

                # Mock get_chat_member for user 300
                member_mock = MagicMock()
                member_mock.status = "member"
                mock_bot.get_chat_member.return_value = member_mock

                await service._update_curators_cache()

                assert "100" in service._curators_cache  # Admin
                assert "200" in service._curators_cache  # Proposer (known in user_repo)
                assert (
                    "300" in service._curators_cache
                )  # Voter (validated via get_chat_member)

    @pytest.mark.asyncio
    async def test_approve(self, service):
        p = Proposal(id="1", from_chat_id=1, from_message_id=1, text="t")
        service.repo.load.return_value = p

        mock_bot = AsyncMock()
        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_app.initialize = AsyncMock()

        with patch("tg.get_tg_application", return_value=mock_app):
            with patch(
                "tg.handlers.utils.callback_query.approve_proposal",
                new_callable=AsyncMock,
            ) as mock_approve:
                res = await service.approve("proposal", "1")
                assert res is True
                mock_approve.assert_called_once_with(p, mock_bot)

    @pytest.mark.asyncio
    async def test_approve_not_found(self, service):
        service.repo.load.return_value = None
        res = await service.approve("proposal", "1")
        assert res is False

    @pytest.mark.asyncio
    async def test_reject_not_found(self, service):
        service.repo.load.return_value = None
        res = await service.reject("Proposal", "1")
        assert res is False

    @pytest.mark.asyncio
    async def test_update_curators_cache_error(self, service):
        with patch("tg.get_tg_application", side_effect=Exception("Boom")):
            await service._update_curators_cache()
            # Should just log error and return
            assert service._last_update is None

    @pytest.mark.asyncio
    async def test_update_curators_cache_member_error(self, service):
        mock_bot = AsyncMock()
        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_app.initialize = AsyncMock()
        from telegram.error import BadRequest

        mock_bot.get_chat_member.side_effect = BadRequest("fail")

        with patch("tg.get_tg_application", return_value=mock_app):
            with patch("services.proposal_service.config") as mock_config:
                mock_config.mod_chat_id = 123
                service.repo.load_all.return_value = [Proposal(id="1", user_id="100")]
                service.long_repo.load_all.return_value = []
                service.user_repo.load_all.return_value = []
                mock_bot.get_chat_administrators.return_value = []

                await service._update_curators_cache()
                # User 100 should NOT be in cache because check failed
                assert "100" not in service._curators_cache

    @pytest.mark.asyncio
    async def test_reject(self, service):
        p = LongProposal(id="1", from_chat_id=1, from_message_id=1, text="t")
        service.long_repo.load.return_value = p

        mock_bot = AsyncMock()
        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_app.initialize = AsyncMock()

        with patch("tg.get_tg_application", return_value=mock_app):
            with patch(
                "tg.handlers.utils.callback_query.dismiss_proposal",
                new_callable=AsyncMock,
            ) as mock_dismiss:
                res = await service.reject("LongProposal", "1")
                assert res is True
                mock_dismiss.assert_called_once_with(p, mock_bot)
