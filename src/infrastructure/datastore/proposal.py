import asyncio
from google.cloud import datastore
from models.proposal import Proposal, LongProposal
from infrastructure.datastore.base import DatastoreRepository
from utils import normalize_str


class ProposalDatastoreRepository(DatastoreRepository[Proposal]):
    def __init__(self, model_class: type[Proposal] | type[LongProposal] = Proposal):
        super().__init__(model_class.kind)
        self.model_class = model_class

    def _entity_to_domain(self, entity: datastore.Entity) -> Proposal:
        entity_id = ""
        if entity.key:
            entity_id = str(entity.key.name)

        return self.model_class(
            id=entity_id,
            from_chat_id=entity["from_chat_id"],
            from_message_id=entity["from_message_id"],
            text=entity["text"],
            liked_by=[str(uid) for uid in entity.get("liked_by", [])],
            disliked_by=[str(uid) for uid in entity.get("disliked_by", [])],
            user_id=entity.get("user_id", 0),
            voting_ended=entity.get("voting_ended", False),
            voting_ended_at=entity.get("voting_ended_at"),
            created_at=entity.get("created_at"),
        )

    def _domain_to_entity(
        self, proposal: Proposal, key: datastore.Key
    ) -> datastore.Entity:
        entity = datastore.Entity(key=key)
        entity.update(proposal.model_dump())
        return entity

    async def load(self, entity_id: str | int) -> Proposal | None:
        def _get():
            key = self.get_key(entity_id)
            entity = self.client.get(key)
            return self._entity_to_domain(entity) if entity else None

        return await asyncio.to_thread(_get)

    async def load_all(self) -> list[Proposal]:
        def _fetch():
            query = self.client.query(kind=self.kind)
            return [self._entity_to_domain(entity) for entity in query.fetch()]

        return await asyncio.to_thread(_fetch)

    async def save(self, proposal: Proposal) -> None:
        def _put():
            key = self.get_key(proposal.id)
            entity = self._domain_to_entity(proposal, key)
            self.client.put(entity)

        await asyncio.to_thread(_put)

    async def get_proposals(
        self, search: str = "", limit: int = 0, offset: int = 0, **filters: object
    ) -> list[Proposal]:
        results = await self.load_all()
        if search:
            norm_search = normalize_str(search)
            results = [p for p in results if norm_search in normalize_str(p.text)]

        for field, value in filters.items():
            if value is None or value == "":
                continue
            if value == "__EMPTY__":
                results = [p for p in results if not getattr(p, field, None)]
            else:
                str_val = str(value).lower()
                results = [
                    p
                    for p in results
                    if str(getattr(p, field, None)).lower() == str_val
                ]

        return results[offset : offset + limit] if limit > 0 else results


# Instances
proposal_repository = ProposalDatastoreRepository(Proposal)
long_proposal_repository = ProposalDatastoreRepository(LongProposal)
