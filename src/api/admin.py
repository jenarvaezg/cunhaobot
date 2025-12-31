import logging
from typing import Annotated, Any
from litestar import Controller, Request, get, post
from litestar.response import Response, Template
from litestar.params import Dependency
from litestar.exceptions import HTTPException
from litestar.datastructures import UploadFile

from services.proposal_service import ProposalService
from infrastructure.protocols import UserRepository
from core.config import config
from tg import get_tg_application

logger = logging.getLogger(__name__)


class AdminController(Controller):
    path = "/admin"

    @get("/broadcast")
    async def broadcast_page(self, request: Request) -> Template:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return Template(
            template_name="broadcast.html",
            context={
                "user": user,
                "owner_id": config.owner_id,
            },
        )

    @post("/broadcast")
    async def broadcast_send(
        self,
        request: Request,
        user_repo: Annotated[UserRepository, Dependency()],
    ) -> Response[str]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        form_data = await request.form()
        message = form_data.get("message")
        upload_file = form_data.get("data")

        content_bytes = b""
        is_video = False
        is_image = False

        if isinstance(upload_file, UploadFile) and upload_file.filename:
            content_bytes = await upload_file.read()
            content_type = upload_file.content_type
            is_video = content_type.startswith("video/") if content_type else False
            is_image = content_type.startswith("image/") if content_type else False

        if not content_bytes and not message:
            return Response(
                "Escribe algo o sube un archivo, alma de cántaro.", status_code=400
            )

        users = user_repo.load_all(ignore_gdpr=False)

        application = get_tg_application()
        await application.initialize()
        bot = application.bot

        success_count = 0
        fail_count = 0

        for u in users:
            if u.platform != "telegram" or u.is_group:
                continue
            try:
                # Convert ID to int if it's numeric
                chat_id = (
                    int(u.id)
                    if isinstance(u.id, str) and u.id.lstrip("-").isdigit()
                    else u.id
                )

                if is_video:
                    await bot.send_video(
                        chat_id=chat_id, video=content_bytes, caption=message
                    )
                elif is_image:
                    await bot.send_photo(
                        chat_id=chat_id, photo=content_bytes, caption=message
                    )
                else:
                    await bot.send_message(chat_id=chat_id, text=message)  # type: ignore[arg-type]

                success_count += 1
            except Exception as e:
                logger.warning(f"Error sending broadcast to {u.id}: {e}")
                # If they blocked us, we count it as a fail but don't stop the broadcast
                u.gdpr = True
                user_repo.save(u)
                fail_count += 1

        return Response(
            f"Difusión completada. ✅ {success_count} enviados, 🚫 {fail_count} fallidos (usuarios que han bloqueado el bot o GDPR activado).",
            status_code=200,
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
