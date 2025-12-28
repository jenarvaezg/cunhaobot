from datetime import date

from google.cloud import datastore

from models.phrase import LongPhrase, Phrase
from models.user import InlineUser, User


class Report:
    kind = "Report"

    def __init__(
        self,
        longs: int,
        shorts: int,
        users: int,
        groups: int,
        inline_users: int,
        inline_usages: int,
        gdprs: int,
        chapas: int,
        top_long: str,
        top_short: str,
        day: int,
        month: int,
        year: int,
    ):
        self.longs = longs
        self.shorts = shorts
        self.users = users
        self.groups = groups
        self.inline_users = inline_users
        self.inline_usages = inline_usages
        self.gdprs = gdprs
        self.chapas = chapas
        self.top_short = top_short
        self.top_long = top_long
        self.day = day
        self.month = month
        self.year = year

    @classmethod
    def generate(
        cls,
        long_phrases: list[LongPhrase],
        short_phrases: list[Phrase],
        users: list[User],
        inline_users: list[InlineUser],
        chapas: list,
        date: date,
    ) -> "Report":
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
            ).text,
            top_short=max(
                short_phrases,
                key=lambda p: p.daily_usages
                + p.audio_daily_usages
                + p.sticker_daily_usages,
            ).text,
            day=date.day,
            month=date.month,
            year=date.year,
        )
        report.save()
        return report

    @property
    def datastore_id(self) -> str:
        return f"{self.year}/{self.month}/{self.day}"

    @classmethod
    def from_entity(cls, entity: datastore.Entity) -> "Report":
        return cls(
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
            day=entity["day"],
            month=entity["month"],
            year=entity["year"],
        )

    def save(self) -> None:
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.datastore_id)
        entity = datastore.Entity(key=key)

        entity["longs"] = self.longs
        entity["shorts"] = self.shorts
        entity["users"] = self.users
        entity["groups"] = self.groups
        entity["inline_users"] = self.inline_users
        entity["inline_usages"] = self.inline_usages
        entity["gdprs"] = self.gdprs
        entity["chapas"] = self.chapas
        entity["top_long"] = self.top_long
        entity["top_short"] = self.top_short
        entity["day"] = self.day
        entity["month"] = self.month
        entity["year"] = self.year

        datastore_client.put(entity)

    @classmethod
    def get_at(cls, day: date) -> "Report":
        datastore_client = datastore.Client()
        query: datastore.Query = datastore_client.query(kind=cls.kind)

        query.add_filter("day", "=", day.day)
        query.add_filter("month", "=", day.month)
        query.add_filter("year", "=", day.year)
        reports = [r for r in query.fetch()]
        return cls.from_entity(reports[0])
