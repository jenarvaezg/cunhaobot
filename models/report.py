from datetime import datetime
from typing import List

from google.cloud import datastore

from models.user import User, InlineUser


class Report:
    kind = 'Report'

    def __init__(self, longs, shorts, users, groups, inline_users, gdprs, chapas, day, month, year):
        self.longs = longs
        self.shorts = shorts
        self.users = users
        self.groups = groups
        self.inline_users = inline_users
        self.gdprs = gdprs
        self.chapas = chapas
        self.day = day
        self.month = month
        self.year = year

    @classmethod
    def generate(
            cls, long_phrases: List, short_phrases: List, users: List[User], inline_users: List[InlineUser],
            chapas: List, date: datetime.date
    ) -> 'Report':
        report = cls(
            len(long_phrases),
            len(short_phrases),
            len([u for u in users if not u.is_group]),
            len([u for u in users if u.is_group]),
            len(inline_users),
            len([u for u in users if u.gdpr]),
            len(chapas),
            date.day,
            date.month,
            date.year,
        )
        report.save()
        return report


    @property
    def datastore_id(self):
        return f'{self.year}/{self.month}/{self.day}'

    @classmethod
    def from_entity(cls, entity) -> 'Report':
        return cls(
            entity['longs'],
            entity['shorts'],
            entity['users'],
            entity['groups'],
            entity['inline_users'],
            entity['gdprs'],
            entity['chapas'],
            entity['day'],
            entity['month'],
            entity['year'],
        )

    def save(self) -> None:
        datastore_client = datastore.Client()
        key = datastore_client.key(self.kind, self.datastore_id)
        entity = datastore.Entity(key=key)

        entity['longs'] = self.longs
        entity['shorts'] = self.shorts
        entity['users'] = self.users
        entity['groups'] = self.groups
        entity['inline_users'] = self.inline_users
        entity['gdprs'] = self.gdprs
        entity['chapas'] = self.chapas
        entity['day'] = self.day
        entity['month'] = self.month
        entity['year'] = self.year

        datastore_client.put(entity)

    @classmethod
    def get_at(cls, day: datetime.date) -> 'Report':
        datastore_client = datastore.Client()
        query: datastore.Query = datastore_client.query(kind=cls.kind)

        query.add_filter('day', '=', day.day)
        query.add_filter('month', '=', day.month)
        query.add_filter('year', '=', day.year)
        reports = [r for r in query.fetch()]
        return cls.from_entity(reports[0])
