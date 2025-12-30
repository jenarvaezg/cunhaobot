import pytest
from unittest.mock import MagicMock
from models.schedule import Schedule
from infrastructure.datastore.schedule import ScheduleDatastoreRepository


class MockEntity(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = MagicMock()


class TestScheduleDatastoreRepository:
    @pytest.fixture
    def repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        from google.cloud import datastore

        datastore.Entity.return_value.reset_mock()
        return ScheduleDatastoreRepository()

    def test_save(self, repo, mock_datastore_client):
        schedule = Schedule(chat_id=1, hour=10, minute=30)
        repo.save(schedule)

        mock_datastore_client.put.assert_called_once()
        # Entity is a mock, we check if update was called
        entity = mock_datastore_client.put.call_args[0][0]
        entity.update.assert_called_once()

        # Check if ID was generated (hard to check directly on entity mock without more complex setup,
        # but we can check if schedule object was updated)
        assert schedule.id == "1_10_30"

    def test_save_with_id(self, repo, mock_datastore_client):
        schedule = Schedule(id="myid", chat_id=1, hour=10, minute=30)
        repo.save(schedule)

        mock_datastore_client.put.assert_called_once()
        entity = mock_datastore_client.put.call_args[0][0]
        # Verify update call
        entity.update.assert_called_once()

    def test_load_all(self, repo, mock_datastore_client):
        query = MagicMock()
        mock_datastore_client.query.return_value = query

        data = {"chat_id": 1, "hour": 10, "minute": 30}
        entity = MockEntity(data)
        entity.key.name = "1_10_30"

        query.fetch.return_value = [entity]

        schedules = repo.load_all()
        assert len(schedules) == 1
        assert schedules[0].id == "1_10_30"
        assert schedules[0].chat_id == 1

    def test_get_schedules(self, repo, mock_datastore_client):
        query = MagicMock()
        mock_datastore_client.query.return_value = query

        d1 = {"chat_id": 1, "hour": 10, "minute": 30}
        e1 = MockEntity(d1)
        e1.key.name = "1"

        d2 = {"chat_id": 2, "hour": 11, "minute": 30}
        e2 = MockEntity(d2)
        e2.key.name = "2"

        query.fetch.return_value = [e1, e2]

        res = repo.get_schedules(chat_id=1)
        assert len(res) == 1
        assert res[0].chat_id == 1

        res2 = repo.get_schedules(minute=30)
        assert len(res2) == 2
