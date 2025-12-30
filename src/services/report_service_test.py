import pytest
from unittest.mock import MagicMock
from datetime import date
from models.phrase import Phrase, LongPhrase
from models.user import User, InlineUser
from services.report_service import ReportService


class TestReportService:
    @pytest.fixture
    def service(self):
        self.report_repo = MagicMock()
        self.phrase_repo = MagicMock()
        self.long_repo = MagicMock()
        self.user_repo = MagicMock()
        self.inline_repo = MagicMock()
        return ReportService(
            self.report_repo,
            self.phrase_repo,
            self.long_repo,
            self.user_repo,
            self.inline_repo,
        )

    def test_generate_report(self, service):
        report_date = date(2025, 12, 30)
        chapas = ["chapa1", "chapa2"]

        # Mock data
        p1 = Phrase(text="short1", daily_usages=10)
        p2 = Phrase(text="short2", daily_usages=5)
        service.phrase_repo.load_all.return_value = [p1, p2]

        l1 = LongPhrase(text="long1", daily_usages=2)
        l2 = LongPhrase(text="long2", daily_usages=20)
        service.long_repo.load_all.return_value = [l1, l2]

        u1 = User(chat_id=1, is_group=False)
        u2 = User(chat_id=2, is_group=True)
        u3 = User(chat_id=3, gdpr=True, is_group=False)
        service.user_repo.load_all.return_value = [u1, u2, u3]

        i1 = InlineUser(user_id=1, usages=5)
        i2 = InlineUser(user_id=2, usages=10)
        service.inline_repo.load_all.return_value = [i1, i2]

        report = service.generate_report(report_date, chapas)

        assert report.longs == 2
        assert report.shorts == 2
        assert report.users == 2  # u1 and u3
        assert report.groups == 1  # u2
        assert report.inline_users == 2
        assert report.inline_usages == 15
        assert report.gdprs == 1  # u3
        assert report.chapas == 2
        assert report.top_short == "short1"
        assert report.top_long == "long2"

        service.report_repo.save.assert_called_once_with(report)

    def test_generate_report_empty(self, service):
        report_date = date(2025, 12, 30)
        chapas = []

        service.phrase_repo.load_all.return_value = []
        service.long_repo.load_all.return_value = []
        service.user_repo.load_all.return_value = []
        service.inline_repo.load_all.return_value = []

        report = service.generate_report(report_date, chapas)

        assert report.longs == 0
        assert report.top_short == ""
        assert report.top_long == ""
        service.report_repo.save.assert_called_once()
