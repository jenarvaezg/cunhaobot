from datetime import date, datetime
from google.cloud import datastore
from models.report import Report
from infrastructure.datastore.base import DatastoreRepository


class ReportDatastoreRepository(DatastoreRepository[Report]):
    def __init__(self):
        super().__init__(Report.kind)

    def _entity_to_domain(self, entity: datastore.Entity) -> Report:
        return Report(**entity)

    def save(self, report: Report) -> None:
        key = self.get_key(report.datastore_id)
        entity = datastore.Entity(key=key)
        entity.update(report.model_dump())
        self.client.put(entity)

    def get_at(self, dt: date) -> Report | None:
        start_dt = datetime.combine(dt, datetime.min.time())
        end_dt = datetime.combine(dt, datetime.max.time())

        query = self.client.query(kind=self.kind)
        query.add_filter("created_at", ">=", start_dt)
        query.add_filter("created_at", "<=", end_dt)

        reports = list(query.fetch(limit=1))
        return self._entity_to_domain(reports[0]) if reports else None

    def load_all(self) -> list[Report]:
        query = self.client.query(kind=self.kind)
        return [self._entity_to_domain(entity) for entity in query.fetch()]


# Instances
report_repository = ReportDatastoreRepository()
