from google.cloud import datastore
from typing import Any
from models.schedule import Schedule
from infrastructure.datastore.base import DatastoreRepository


class ScheduleDatastoreRepository(DatastoreRepository[Schedule]):
    def __init__(self):
        super().__init__(Schedule.kind)

    def _entity_to_domain(self, entity: datastore.Entity) -> Schedule:
        data = dict(entity)
        data["id"] = str(entity.key.name)
        return Schedule(**data)

    def load_all(self) -> list[Schedule]:
        query = self.client.query(kind=self.kind)
        return [self._entity_to_domain(entity) for entity in query.fetch()]

    def get_schedules(self, **filters: Any) -> list[Schedule]:
        results = self.load_all()
        for field, value in filters.items():
            if value is not None:
                results = [s for s in results if getattr(s, field, None) == value]
        return results

    def save(self, schedule: Schedule) -> None:
        if not schedule.id:
            schedule.id = f"{schedule.chat_id}_{schedule.hour}_{schedule.minute}"

        key = self.get_key(schedule.id)
        entity = datastore.Entity(key=key)
        entity.update(schedule.model_dump())
        self.client.put(entity)


schedule_repository = ScheduleDatastoreRepository()
