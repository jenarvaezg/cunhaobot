from models.user import User, InlineUser


class TestUser:
    def test_user_init(self):
        user = User(chat_id=123, name="Test User", is_group=False)
        assert user.chat_id == 123
        assert user.name == "Test User"
        assert not user.is_group
        assert not user.gdpr


class TestInlineUser:
    def test_inline_user_init(self):
        user = InlineUser(user_id=456, name="Inline User", usages=10)
        assert user.user_id == 456
        assert user.name == "Inline User"
        assert user.usages == 10
