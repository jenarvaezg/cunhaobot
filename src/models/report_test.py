import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from models.report import Report
from models.phrase import Phrase, LongPhrase
from models.user import User, InlineUser


def create_mock_entity(data):
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.get.side_effect = data.get

    def setitem(key, value):
        data[key] = value

    m.__setitem__.side_effect = setitem
    m.update.side_effect = data.update
    return m


class TestReport:
    @pytest.fixture(autouse=True)
    def setup(self, mock_datastore_client):
        self.mock_client = mock_datastore_client
        self.mock_client.reset_mock()

    def test_init(self):
        report = Report(
            longs=10,
            shorts=20,
            users=5,
            groups=2,
            inline_users=3,
            inline_usages=100,
            gdprs=0,
            chapas=1,
            top_long="L",
            top_short="S",
            day=1,
            month=1,
            year=2025,
        )
        assert report.longs == 10
        assert report.datastore_id == "2025/1/1"

    def test_generate(self):
        long_phrases = [LongPhrase(text="Long 1"), LongPhrase(text="Long 2")]
        short_phrases = [Phrase(text="Short 1")]
        users = [User(1, "U1", False), User(2, "G1", True, gdpr=True)]
        inline_users = [InlineUser(3, "I1", 5)]
        chapas = [1, 2, 3]

        for p in long_phrases + short_phrases:
            p.daily_usages = 0
            p.audio_daily_usages = 0
            p.sticker_daily_usages = 0

        with patch("models.report.Report.save"):
            report = Report.generate(
                long_phrases,
                short_phrases,
                users,
                inline_users,
                chapas,
                date(2025, 12, 28),
            )

            assert report.longs == 2
            assert report.shorts == 1
            assert report.users == 1
            assert report.groups == 1
            assert report.gdprs == 1
            assert report.inline_users == 1
            assert report.inline_usages == 5
            assert report.chapas == 3
            assert report.day == 28

    def test_from_entity(self):
        data = {
            "longs": 1,
            "shorts": 2,
            "users": 3,
            "groups": 4,
            "inline_users": 5,
            "inline_usages": 6,
            "gdprs": 7,
            "chapas": 8,
            "top_long": "TL",
            "top_short": "TS",
            "day": 28,
            "month": 12,
            "year": 2025,
        }
        entity = create_mock_entity(data)
        repo = Report.get_repository()
        report = repo._entity_to_domain(entity)
        assert report.longs == 1
        assert report.top_long == "TL"

    def test_save(self):
        report = Report(1, 2, 3, 4, 5, 6, 7, 8, "TL", "TS", 28, 12, 2025)
        report.save()
        self.mock_client.key.assert_called_with("Report", "2025/12/28")
        self.mock_client.put.assert_called()

    def test_get_at(self):
        data = {
            "longs": 1,
            "shorts": 2,
            "users": 3,
            "groups": 4,
            "inline_users": 5,
            "inline_usages": 6,
            "gdprs": 7,
            "chapas": 8,
            "top_long": "TL",
            "top_short": "TS",
            "day": 28,
            "month": 12,
            "year": 2025,
        }
        e = create_mock_entity(data)
        self.mock_client.query.return_value.fetch.return_value = [e]
        report = Report.get_at(date(2025, 12, 28))
        assert report.longs == 1
        assert self.mock_client.query.return_value.add_filter.call_count == 3
