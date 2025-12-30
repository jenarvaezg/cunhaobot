from typing import Annotated, Any
from litestar import Controller, Request, post
from litestar.response import Response
from litestar.params import Dependency

from services.proposal_service import ProposalService
from core.config import config


class AdminController(Controller):
    path = "/admin"

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
