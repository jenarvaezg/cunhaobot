from datetime import datetime
from models.report import Report


class TestReport:
    def test_report_init(self):
        report = Report(
            longs=1,
            shorts=2,
            users=3,
            groups=4,
            inline_users=5,
            inline_usages=6,
            gdprs=7,
            chapas=8,
            top_long="TL",
            top_short="TS",
            created_at=datetime.now(),
        )
        assert report.longs == 1
        assert report.top_long == "TL"

    def test_datastore_id(self):
        report = Report(
            longs=0,
            shorts=0,
            users=0,
            groups=0,
            inline_users=0,
            inline_usages=0,
            gdprs=0,
            chapas=0,
            top_long="",
            top_short="",
            created_at=datetime(2025, 12, 30),
        )
        assert report.datastore_id == "2025/12/30"

    def test_datastore_id_none_created_at(self):
        report = Report(
            longs=0,
            shorts=0,
            users=0,
            groups=0,
            inline_users=0,
            inline_usages=0,
            gdprs=0,
            chapas=0,
            top_long="",
            top_short="",
            created_at=None,  # Explicitly set created_at to None
        )
        assert report.datastore_id == "unknown"
