import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram.constants import ChatType
from models.user import User
from services.user_service import UserService


class TestUserService:
    @pytest.fixture
    def service(self):
        self.user_repo = AsyncMock()
        self.chat_repo = AsyncMock()
        self.phrase_repo = AsyncMock()
        self.long_phrase_repo = AsyncMock()
        self.proposal_repo = AsyncMock()
        self.long_proposal_repo = AsyncMock()
        self.link_request_repo = AsyncMock()
        return UserService(
            self.user_repo,
            self.chat_repo,
            self.phrase_repo,
            self.long_phrase_repo,
            self.proposal_repo,
            self.long_proposal_repo,
            self.link_request_repo,
        )

    @pytest.mark.asyncio
    async def test_update_or_create_user_new(self, service):
        update = MagicMock()
        update.effective_message.chat_id = 123
        update.effective_message.chat.type = ChatType.PRIVATE
        update.effective_message.chat.title = None
        update.effective_message.chat.username = None
        update.effective_user.id = 123
        update.effective_user.name = "New User"
        update.effective_user.username = "new_user"

        service.user_repo.load.return_value = None
        service.chat_repo.load.return_value = None

        user = await service.update_or_create_user(update)
        assert user.id == 123
        assert user.name == "New User"
        assert user.username == "new_user"
        service.user_repo.save.assert_called_once()
        service.chat_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_or_create_user_update(self, service):
        update = MagicMock()
        update.effective_message.chat_id = 123
        update.effective_message.chat.type = ChatType.PRIVATE
        update.effective_message.chat.title = None
        update.effective_message.chat.username = None
        update.effective_user.id = 123
        update.effective_user.name = "Updated User"
        update.effective_user.username = "updated_user"

        existing = User(id=123, name="Old", gdpr=True)
        service.user_repo.load.return_value = existing
        service.chat_repo.load.return_value = MagicMock()

        user = await service.update_or_create_user(update)
        assert user.name == "Updated User"
        assert user.username == "updated_user"
        assert user.gdpr is False
        service.user_repo.save.assert_called_once_with(existing)

    @pytest.mark.asyncio
    async def test_update_or_create_user_group(self, service):
        update = MagicMock()
        update.effective_message.chat_id = -456
        update.effective_message.chat.type = ChatType.GROUP
        update.effective_message.chat.title = "My Group"
        update.effective_message.chat.username = "my_group_user"
        update.effective_user.id = 123
        update.effective_user.name = "Person"
        update.effective_user.username = "person_user"

        service.user_repo.load.return_value = None
        service.chat_repo.load.return_value = None

        user = await service.update_or_create_user(update)
        # Should return the person, not the group
        assert user.id == 123
        assert user.name == "Person"

        # Should have saved both
        assert service.user_repo.save.called
        assert service.chat_repo.save.called

        # Verify chat call
        chat_call = service.chat_repo.save.call_args[0][0]
        assert chat_call.id == -456
        assert chat_call.title == "My Group"
        assert chat_call.type == ChatType.GROUP

    @pytest.mark.asyncio
    async def test_update_or_create_user_no_message(self, service):
        update = MagicMock()
        update.effective_message = None
        assert await service.update_or_create_user(update) is None

    @pytest.mark.asyncio
    async def test_update_or_create_inline_user_new(self, service):
        update = MagicMock()
        update.effective_user.id = 789
        update.effective_user.name = "New Inline"
        update.effective_user.username = "new_inline"

        service.user_repo.load.return_value = None

        user = await service.update_or_create_inline_user(update)
        assert user.id == 789
        assert user.username == "new_inline"
        service.user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_hard(self, service):
        user = User(id=123)
        await service.delete_user(user, hard=True)
        service.user_repo.delete.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_delete_user_soft(self, service):
        user = User(id=123, gdpr=False)
        await service.delete_user(user, hard=False)
        assert user.gdpr is True
        service.user_repo.save.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_add_inline_usage(self, service):
        user = User(id=123, usages=5, points=0)
        await service.add_inline_usage(user)
        assert user.usages == 6
        assert user.points == 1
        service.user_repo.save.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_add_points(self, service):
        user_id = 123
        points = 10

        user = User(id=user_id, points=5)
        service.user_repo.load.return_value = user

        await service.add_points(user_id, points)

        assert user.points == 15
        service.user_repo.save.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_add_points_not_found(self, service):
        service.user_repo.load.return_value = None
        await service.add_points(123, 10)
        service.user_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_points_zero_id(self, service):
        await service.add_points(0, 10)
        service.user_repo.load.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_photo_slack_id(self, service):
        # Slack IDs are strings like 'U12345'
        photo = await service.get_user_photo("U12345")
        assert photo is None

    @pytest.mark.asyncio
    async def test_get_user_photo_empty_id(self, service):
        assert await service.get_user_photo("") is None
        assert await service.get_user_photo(None) is None

    @pytest.mark.asyncio
    async def test_get_user_photo_telegram_success(self, service):
        with patch("tg.get_tg_application") as mock_get_app:
            mock_app = MagicMock()
            mock_app.initialize = AsyncMock()
            mock_get_app.return_value = mock_app
            mock_app.running = False

            mock_photos = MagicMock()
            mock_photos.total_count = 1
            mock_photo = MagicMock()
            mock_photo.file_id = "file123"
            mock_photos.photos = [[mock_photo]]
            mock_app.bot.get_user_profile_photos = AsyncMock(return_value=mock_photos)

            mock_file = MagicMock()
            mock_file.download_as_bytearray = AsyncMock(return_value=b"photo_bytes")
            mock_app.bot.get_file = AsyncMock(return_value=mock_file)

            photo = await service.get_user_photo(12345)
            assert photo == b"photo_bytes"
            mock_app.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_photo_telegram_no_photos(self, service):
        with patch("tg.get_tg_application") as mock_get_app:
            mock_app = MagicMock()
            mock_get_app.return_value = mock_app
            mock_app.running = True

            mock_photos = MagicMock()
            mock_photos.total_count = 0
            mock_app.bot.get_user_profile_photos = AsyncMock(return_value=mock_photos)

            photo = await service.get_user_photo(12345)
            assert photo is None

    @pytest.mark.asyncio
    async def test_get_user_photo_telegram_error(self, service):
        with patch("tg.get_tg_application") as mock_get_app:
            mock_app = MagicMock()
            mock_get_app.return_value = mock_app
            mock_app.running = True
            mock_app.bot.get_user_profile_photos = AsyncMock(
                side_effect=Exception("TG Error")
            )

            photo = await service.get_user_photo(12345)
            assert photo is None

    @pytest.mark.asyncio
    async def test_get_user_fallback(self, service):
        user = User(id=123)

        def load_side_effect(uid):
            if uid == "123":
                return None
            if uid == 123:
                return user
            return None

        service.user_repo.load.side_effect = load_side_effect

        # Call with string, expecting fallback to int
        result = await service.get_user("123")
        assert result == user
        assert result.id == 123

    @pytest.mark.asyncio
    async def test_get_user_fallback_negative(self, service):
        user = User(id=-456)

        def load_side_effect(uid):
            if uid == "-456":
                return None
            if uid == -456:
                return user
            return None

        service.user_repo.load.side_effect = load_side_effect

        result = await service.get_user("-456")
        assert result == user
        assert result.id == -456
