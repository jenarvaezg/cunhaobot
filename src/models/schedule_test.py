import pytest
from unittest.mock import MagicMock
from models.schedule import ScheduledTask


def create_mock_entity(data):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get

    def setitem(key, value):
        data[key] = value

    m.__setitem__.side_effect = setitem
    m.update.side_effect = data.update
    return m


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

        data = {
            "chat_id": 123,
            "hour": 10,
            "minute": 30,
            "query": "q",
            "service": "s",
            "type": "t",
        }
        e = create_mock_entity(data)
        mock_query.fetch.return_value = [e]

        tasks = ScheduledTask.get_tasks(chat_id=123)
        assert len(tasks) == 1
        assert tasks[0].chat_id == 123
        self.mock_client.query.assert_called_with(kind="ScheduledTask")

    def test_delete(self):
        task = ScheduledTask(123, 10, 30, "query", "telegram", "chapa")
        task.delete()
        self.mock_client.delete.assert_called()
