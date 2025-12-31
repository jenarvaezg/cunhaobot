import logging
from typing import Annotated, Any
from litestar import Controller, Request, post, get
from litestar.response import Response, Redirect
from litestar.params import Dependency
from litestar.plugins.htmx import HTMXTemplate

from services.proposal_service import ProposalService
from services.user_service import UserService
from core.config import config

logger = logging.getLogger(__name__)


class AdminController(Controller):
    path = "/admin"

    @get("/broadcast")
    async def get_broadcast(self, request: Request) -> HTMXTemplate | Redirect:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Redirect(path="/")

        return HTMXTemplate(
            template_name="broadcast.html", context={"owner_id": config.owner_id}
        )

    @post("/broadcast")
    async def post_broadcast(
        self,
        request: Request,
        user_service: Annotated[UserService, Dependency()],
    ) -> HTMXTemplate:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return HTMXTemplate(
                template_name="partials/broadcast_result.html",
                context={
                    "error": True,
                    "message": "Pirate de aquí, que no eres el jefe.",
                },
            )

        data = await request.form()
        message = data.get("message")
        if not message:
            return HTMXTemplate(
                template_name="partials/broadcast_result.html",
                context={"error": True, "message": "Escribe algo, alma de cántaro."},
            )

        # Get all telegram users
        all_users = user_service.user_repo.load_all(ignore_gdpr=False)
        telegram_users = [
            u for u in all_users if u.platform == "telegram" and not u.is_group
        ]

        from tg import get_tg_application

        application = get_tg_application()
        bot = application.bot

        success_count = 0
        blocked_count = 0

        for u in telegram_users:
            try:
                # Convert ID to int if it's numeric
                chat_id = (
                    int(u.id)
                    if isinstance(u.id, str) and u.id.lstrip("-").isdigit()
                    else u.id
                )
                await bot.send_message(chat_id=chat_id, text=message)  # type: ignore[arg-type]
                success_count += 1
            except Exception as e:
                logger.warning(
                    f"Error sending message to {u.id}, assuming permission lost: {e}"
                )
                u.gdpr = True
                user_service.user_repo.save(u)
                blocked_count += 1

        result_message = f"¡Difusión completada! ✅ {success_count} enviados, 🚫 {blocked_count} fallidos/bloqueados (GDPR activado)."

        return HTMXTemplate(
            template_name="partials/broadcast_result.html",
            context={"message": result_message},
        )

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
