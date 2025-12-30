from typing import Annotated, Any
from litestar import Controller, Request, get, post
from litestar.response import Response, Template
from litestar.params import Dependency

from services.proposal_service import ProposalService
from core.config import config


class AdminController(Controller):
    path = "/admin"

    @get("/orphans")
    async def orphans(
        self,
        request: Request,
        phrase_repo: Annotated[Any, Dependency()],
        long_phrase_repo: Annotated[Any, Dependency()],
        proposal_service: Annotated[Any, Dependency()],
    ) -> Template | Response:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        orphan_short = [p for p in phrase_repo.load_all() if not p.proposal_id]
        orphan_long = [p for p in long_phrase_repo.load_all() if not p.proposal_id]

        service: ProposalService = proposal_service
        curators = await service.get_curators()
        sorted_known_users = sorted(
            [{"id": str(uid), "name": name} for uid, name in curators.items()],
            key=lambda x: x["name"].lower(),
        )

        orphan_data = []
        for p in orphan_short[:50]:
            orphan_data.append({"text": p.text, "kind": "Phrase"})
        for p in orphan_long[:50]:
            orphan_data.append({"text": p.text, "kind": "LongPhrase"})

        return Template(
            template_name="orphans.html",
            context={
                "orphans": orphan_data,
                "known_users": sorted_known_users,
                "user": user,
                "owner_id": config.owner_id,
            },
        )

    @post("/orphans/link")
    async def link_orphan(
        self,
        request: Request,
        phrase_repo: Annotated[Any, Dependency()],
        long_phrase_repo: Annotated[Any, Dependency()],
    ) -> Response[str]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        data = await request.json()
        phrase_text = data.get("phrase_text")
        kind = data.get("kind")
        proposal_id = data.get("proposal_id")

        repo = phrase_repo if kind == "Phrase" else long_phrase_repo
        phrase = repo.load(phrase_text)

        if not phrase:
            return Response("Phrase not found", status_code=404)

        phrase.proposal_id = proposal_id
        repo.save(phrase)
        return Response("Linked", status_code=200)

    @post("/orphans/manual-link")
    async def manual_link(
        self,
        request: Request,
        phrase_repo: Annotated[Any, Dependency()],
        long_phrase_repo: Annotated[Any, Dependency()],
    ) -> Response[str]:
        from datetime import datetime

        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        data = await request.json()
        phrase_text = data.get("phrase_text")
        kind = data.get("kind")
        creator_id = int(data.get("creator_id", 0))
        chat_id = int(data.get("chat_id", 0))
        date_str = data.get("date")

        repo = phrase_repo if kind == "Phrase" else long_phrase_repo
        phrase = repo.load(phrase_text)

        if not phrase:
            return Response("Phrase not found", status_code=404)

        phrase.proposal_id = ""
        phrase.user_id = creator_id
        phrase.chat_id = chat_id
        if date_str:
            phrase.created_at = datetime.fromisoformat(date_str)

        repo.save(phrase)
        return Response("Linked", status_code=200)

    @post("/proposals/{kind:str}/{proposal_id:str}/approve")
    async def approve_proposal(
        self,
        kind: str,
        proposal_id: str,
        request: Request,
        proposal_service: Annotated[Any, Dependency()],
    ) -> Response[str]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        service: ProposalService = proposal_service
        if await service.approve(kind, proposal_id):
            return Response("Approved", status_code=200)
        return Response("Not found", status_code=404)

    @post("/proposals/{kind:str}/{proposal_id:str}/reject")
    async def reject_proposal(
        self,
        kind: str,
        proposal_id: str,
        request: Request,
        proposal_service: Annotated[Any, Dependency()],
    ) -> Response[str]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        service: ProposalService = proposal_service
        if await service.reject(kind, proposal_id):
            return Response("Rejected", status_code=200)
        return Response("Not found", status_code=404)
