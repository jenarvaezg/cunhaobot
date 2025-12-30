import pytest
from unittest.mock import MagicMock
from datetime import date, datetime
from models.report import Report
from infrastructure.datastore.report import ReportDatastoreRepository


class TestReportDatastoreRepository:
    @pytest.fixture
    def repo(self, mock_datastore_client):
        mock_datastore_client.reset_mock()
        from google.cloud import datastore

        datastore.Entity.return_value.reset_mock()
        return ReportDatastoreRepository()

    def test_save(self, repo, mock_datastore_client):
        # Fill all fields required by Report model
        report = Report(
            longs=1,
            shorts=1,
            users=0,
            groups=0,
            inline_users=0,
            inline_usages=0,
            gdprs=0,
            chapas=0,
            top_long="l",
            top_short="s",
            created_at=datetime(2025, 12, 30),
        )
        repo.save(report)

        mock_datastore_client.put.assert_called_once()
        entity = mock_datastore_client.put.call_args[0][0]

        # Verify update was called with correct data
        entity.update.assert_called_once()
        args = entity.update.call_args[0][0]
        assert args["longs"] == 1

        # Key check depends on mock structure, skipping explicit key check
        # as we verified put is called with the entity.

    def test_get_at(self, repo, mock_datastore_client):
        query = MagicMock()
        mock_datastore_client.query.return_value = query

        mock_entity = {
            "longs": 5,
            "shorts": 3,
            "created_at": datetime(2025, 12, 30),
            "users": 0,
            "groups": 0,
            "inline_users": 0,
            "inline_usages": 0,
            "gdprs": 0,
            "chapas": 0,
            "top_long": "",
            "top_short": "",
        }
        query.fetch.return_value = [mock_entity]

        dt = date(2025, 12, 30)
        report = repo.get_at(dt)

        assert report.longs == 5
        assert report.created_at == datetime(2025, 12, 30)

        # Check filters
        assert query.add_filter.call_count == 2

    def test_get_at_none(self, repo, mock_datastore_client):
        query = MagicMock()
        mock_datastore_client.query.return_value = query
        query.fetch.return_value = []
        assert repo.get_at(date(2025, 12, 30)) is None

    def test_load_all(self, repo, mock_datastore_client):
        query = MagicMock()
        mock_datastore_client.query.return_value = query
        mock_entity = {
            "longs": 5,
            "shorts": 3,
            "created_at": datetime(2025, 12, 30),
            "users": 0,
            "groups": 0,
            "inline_users": 0,
            "inline_usages": 0,
            "gdprs": 0,
            "chapas": 0,
            "top_long": "",
            "top_short": "",
        }
        query.fetch.return_value = [mock_entity]
        reports = repo.load_all()
        assert len(reports) == 1
        assert reports[0].longs == 5
