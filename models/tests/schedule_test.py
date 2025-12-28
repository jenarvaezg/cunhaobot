import pytest
from unittest.mock import MagicMock
from models.schedule import ScheduledTask


class TestScheduledTask:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        self.mock_client = mock_datastore_client
        self.mock_client.reset_mock()

    def test_init(self):
        task = ScheduledTask(123, 10, 30, "query", "telegram", "chapa")
        assert task.chat_id == 123
        assert task.hour == 10
        assert task.minute == 30
        assert "10:30" in str(task)

    def test_save(self):
        task = ScheduledTask(123, 10, 30, "query", "telegram", "chapa")
        task.save()
        self.mock_client.put.assert_called()

    def test_get_tasks(self):
        mock_query = MagicMock()
        self.mock_client.query.return_value = mock_query

        # from_entity expects a dict-like or entity object
        mock_query.fetch.return_value = [
            {
                "chat_id": 123,
                "hour": 10,
                "minute": 30,
                "query": "q",
                "service": "s",
                "type": "t",
            }
        ]

        tasks = ScheduledTask.get_tasks(chat_id=123)
        assert len(tasks) == 1
        assert tasks[0].chat_id == 123
        self.mock_client.query.assert_called_with(kind="ScheduledTask")

    def test_delete(self):
        task = ScheduledTask(123, 10, 30, "query", "telegram", "chapa")
        task.delete()
        self.mock_client.delete.assert_called()
