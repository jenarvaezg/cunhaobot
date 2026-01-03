import logging
import asyncio
import json
from typing import Annotated, AsyncIterable
from litestar import Controller, Request, get, post
from litestar.response import Response, Template, ServerSentEvent
from litestar.params import Dependency
from litestar.exceptions import HTTPException
from litestar.datastructures import UploadFile

from services.proposal_service import ProposalService
from infrastructure.protocols import UserRepository, ChatRepository
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

    @get("/broadcast/status")
    async def broadcast_status(
        self,
        request: Request,
        user_repo: Annotated[UserRepository, Dependency()],
        chat_repo: Annotated[ChatRepository, Dependency()],
    ) -> ServerSentEvent:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async def progress_generator() -> AsyncIterable[str]:
            msg = request.query_params.get("message")
            include_groups = request.query_params.get("include_groups") == "true"

            # Use CHATS as the source of truth for messaging
            chats = await chat_repo.load_all()

            # Filter targets: active telegram chats
            targets = [c for c in chats if c.platform == "telegram" and c.is_active]

            if not include_groups:
                targets = [c for c in targets if c.type == "private"]
            # If include_groups is True, we take all active chats (both private and groups)

            total = len(targets)

            if total == 0:
                yield json.dumps(
                    {
                        "progress": 100,
                        "current_user": "No hay chats activos",
                        "status": "completed",
                    }
                )
                return

            application = get_tg_application()
            await application.initialize()
            bot = application.bot

            success_count = 0
            fail_count = 0

            for i, target in enumerate(targets):
                progress = int((i / total) * 100)
                yield json.dumps(
                    {
                        "progress": progress,
                        "current_user": target.title
                        or target.username
                        or str(target.id),
                        "status": f"Enviando a {i + 1}/{total}...",
                    }
                )

                try:
                    chat_id = (
                        int(target.id)
                        if isinstance(target.id, str)
                        and target.id.lstrip("-").isdigit()
                        else target.id
                    )
                    await bot.send_message(chat_id=chat_id, text=msg)  # type: ignore[arg-type]
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Error sending broadcast to chat {target.id}: {e}")
                    # Mark chat as inactive if we can't send messages
                    target.is_active = False
                    await chat_repo.save(target)
                    fail_count += 1

                await asyncio.sleep(0.05)

            yield json.dumps(
                {
                    "progress": 100,
                    "current_user": "¡Terminado!",
                    "status": f"Completado. ✅ {success_count} ok, 🚫 {fail_count} fallidos.",
                }
            )

        return ServerSentEvent(progress_generator(), event_type="progress")

    @post("/broadcast")
    async def broadcast_send(
        self,
        request: Request,
        user_repo: Annotated[UserRepository, Dependency()],
        chat_repo: Annotated[ChatRepository, Dependency()],
    ) -> Response[str]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        form_data = await request.form()
        message = str(form_data.get("message") or "")
        upload_file = form_data.get("data")
        include_groups = form_data.get("include_groups") == "true"

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

        # Get targets from Chat repository
        all_chats = await chat_repo.load_all()
        targets = [c for c in all_chats if c.platform == "telegram" and c.is_active]

        if not include_groups:
            targets = [c for c in targets if c.type == "private"]

        application = get_tg_application()
        await application.initialize()
        bot = application.bot

        success_count = 0
        fail_count = 0

        for target in targets:
            try:
                chat_id = (
                    int(target.id)
                    if isinstance(target.id, str) and target.id.lstrip("-").isdigit()
                    else target.id
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
                logger.warning(f"Error sending broadcast to chat {target.id}: {e}")
                target.is_active = False
                await chat_repo.save(target)
                fail_count += 1

        return Response(
            f"Difusión completada. ✅ {success_count} enviados, 🚫 {fail_count} fallidos.",
            status_code=200,
        )

    @post("/proposals/{kind:str}/{proposal_id:str}/approve")
    async def approve_proposal(
        self,
        kind: str,
        proposal_id: str,
        request: Request,
        proposal_service: Annotated[ProposalService, Dependency()],
    ) -> Response[str]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        if await proposal_service.approve(kind, proposal_id):
            return Response("Approved", status_code=200)
        return Response("Not found", status_code=404)

    @post("/proposals/{kind:str}/{proposal_id:str}/reject")
    async def reject_proposal(
        self,
        kind: str,
        proposal_id: str,
        request: Request,
        proposal_service: Annotated[ProposalService, Dependency()],
    ) -> Response[str]:
        user = request.session.get("user")
        if not user or str(user.get("id")) != config.owner_id:
            return Response("Unauthorized", status_code=401)

        if await proposal_service.reject(kind, proposal_id):
            return Response("Rejected", status_code=200)
        return Response("Not found", status_code=404)
