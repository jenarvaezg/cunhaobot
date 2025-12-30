from models.schedule import Schedule


class TestSchedule:
    def test_schedule_init(self):
        s = Schedule(id="1", chat_id=123, user_id=456, hour=10, minute=30, query="test")
        assert s.hour == 10
        assert s.query == "test"
