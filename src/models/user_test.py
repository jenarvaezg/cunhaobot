from models.user import User


class TestUser:
    def test_user_init(self):
        user = User(id=123, name="Test User", is_group=False)
        assert user.id == 123
        assert user.name == "Test User"
        assert not user.is_group
        assert not user.gdpr
        assert user.points == 0
        assert user.usages == 0

    def test_user_with_points_and_usages(self):
        user = User(id=123, name="Test User", points=100, usages=50)
        assert user.points == 100
        assert user.usages == 50
