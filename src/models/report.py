from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, ClassVar, Protocol

from google.cloud import datastore

from utils.gcp import get_datastore_client

if TYPE_CHECKING:
    from models.phrase import LongPhrase, Phrase
    from models.user import InlineUser, User


@dataclass(unsafe_hash=True)
class Report:
    longs: int
    shorts: int
    users: int
    groups: int
    inline_users: int
    inline_usages: int
    gdprs: int
    chapas: int
    top_long: str
    top_short: str
    created_at: datetime = field(default_factory=datetime.now)

    kind: ClassVar[str] = "Report"

    @classmethod
    def generate(
        cls,
        long_phrases: list["LongPhrase"],
        short_phrases: list["Phrase"],
        users: list["User"],
        inline_users: list["InlineUser"],
        chapas: list,
        report_date: date,
    ) -> "Report":
        # report_date is used to set the time to midnight of that day
        created_at = datetime.combine(report_date, datetime.min.time())
        report = cls(
            longs=len(long_phrases),
            shorts=len(short_phrases),
            users=len([u for u in users if not u.is_group]),
            groups=len([u for u in users if u.is_group]),
            inline_users=len(inline_users),
            inline_usages=sum(u.usages for u in inline_users),
            gdprs=len([u for u in users if u.gdpr]),
            chapas=len(chapas),
            top_long=max(
                long_phrases,
                key=lambda p: p.daily_usages
                + p.audio_daily_usages
                + p.sticker_daily_usages,
            ).text
            if long_phrases
            else "",
            top_short=max(
                short_phrases,
                key=lambda p: p.daily_usages
                + p.audio_daily_usages
                + p.sticker_daily_usages,
            ).text
            if short_phrases
            else "",
            created_at=created_at,
        )
        report.save()
        return report

    @property
    def datastore_id(self) -> str:
        return self.created_at.strftime("%Y/%m/%d")

    @classmethod
    def get_repository(cls) -> "ReportRepository":
        return _report_repository

    def save(self) -> None:
        self.get_repository().save(self)

    @classmethod
    def get_at(cls, dt: date) -> "Report | None":
        return cls.get_repository().get_at(dt)


# --- Repository Protocol ---


class ReportRepository(Protocol):
    def save(self, report: Report) -> None: ...
    def get_at(self, dt: date) -> "Report | None": ...


# --- Datastore Implementation ---


class DatastoreReportRepository:
    def __init__(self, model_class: type[Report]):
        self.model_class = model_class

    @property
    def client(self) -> datastore.Client:
        return get_datastore_client()

    def _entity_to_domain(self, entity: datastore.Entity) -> Report:
        return self.model_class(
            longs=entity["longs"],
            shorts=entity["shorts"],
            users=entity["users"],
            groups=entity["groups"],
            inline_users=entity["inline_users"],
            inline_usages=entity["inline_usages"],
            gdprs=entity["gdprs"],
            chapas=entity["chapas"],
            top_long=entity.get("top_long", ""),
            top_short=entity.get("top_short", ""),
            created_at=entity.get("created_at", datetime.now()),
        )

    def save(self, report: Report) -> None:
        key = self.client.key(self.model_class.kind, report.datastore_id)
        entity = datastore.Entity(key=key)
        entity.update(
            {
                "longs": report.longs,
                "shorts": report.shorts,
                "users": report.users,
                "groups": report.groups,
                "inline_users": report.inline_users,
                "inline_usages": report.inline_usages,
                "gdprs": report.gdprs,
                "chapas": report.chapas,
                "top_long": report.top_long,
                "top_short": report.top_short,
                "created_at": report.created_at,
            }
        )
        self.client.put(entity)

    def get_at(self, dt: date) -> "Report | None":
        # Search by created_at range (start and end of day)
        start_dt = datetime.combine(dt, datetime.min.time())
        end_dt = datetime.combine(dt, datetime.max.time())

        query = self.client.query(kind=self.model_class.kind)
        query.add_filter("created_at", ">=", start_dt)
        query.add_filter("created_at", "<=", end_dt)

        reports = list(query.fetch(limit=1))
        if reports:
            return self._entity_to_domain(reports[0])
        return None


# --- Instance ---

_report_repository = DatastoreReportRepository(Report)
