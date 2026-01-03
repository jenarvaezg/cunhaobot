import logging
from typing import Annotated
from litestar import Litestar, Request, get
from litestar.response import Redirect
from litestar.template.config import TemplateConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.static_files import create_static_files_router
from litestar.di import Provide
from litestar.params import Dependency

from core.config import config
from api import WebController, AdminController
from api.slack import SlackController
from api.bot import BotController
from api.utils import get_proposals_context
from utils import verify_telegram_auth
from utils.ui import apelativo
from infrastructure.protocols import ProposalRepository, LongProposalRepository

from services import (
    phrase_repo,
    long_phrase_repo,
    proposal_repo,
    long_proposal_repo,
    user_repo,
    inline_user_repo,
    chat_repo,
    phrase_service,
    proposal_service,
    ai_service,
    user_service,
)

# Enable logging
logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


@get("/auth/telegram")
async def auth_telegram(request: Request) -> Redirect:
    if not verify_telegram_auth(dict(request.query_params), config.tg_token):
        return Redirect(path="/")
    request.set_session(
        {
            "user": {
                "id": request.query_params.get("id"),
                "first_name": request.query_params.get("first_name"),
                "username": request.query_params.get("username"),
                "photo_url": request.query_params.get("photo_url"),
            }
        }
    )
    return Redirect(path="/")


@get("/logout")
async def logout(request: Request) -> Redirect:
    request.clear_session()
    return Redirect(path="/")


@get("/proposals/search")
async def proposals_search(
    request: Request,
    proposal_repo: Annotated[ProposalRepository, Dependency()],
    long_proposal_repo: Annotated[LongProposalRepository, Dependency()],
) -> HTMXTemplate:
    return HTMXTemplate(
        template_name="partials/proposals_list.html",
        context=await get_proposals_context(request, proposal_repo, long_proposal_repo),
    )


@get("/ping")
async def ping() -> str:
    return "I am alive"


def auto_login_local(request: Request) -> None:
    if config.is_gae or request.session.get("user"):
        return
    request.set_session(
        {
            "user": {
                "id": config.owner_id,
                "first_name": "Local",
                "username": "local_owner",
            }
        }
    )


app = Litestar(
    route_handlers=[
        WebController,
        AdminController,
        SlackController,
        BotController,
        auth_telegram,
        logout,
        proposals_search,
        ping,
        create_static_files_router(directories=["src/static"], path="/static"),
    ],
    dependencies={
        "phrase_service": Provide(lambda: phrase_service, sync_to_thread=False),
        "proposal_service": Provide(lambda: proposal_service, sync_to_thread=False),
        "ai_service": Provide(lambda: ai_service, sync_to_thread=False),
        "user_service": Provide(lambda: user_service, sync_to_thread=False),
        "phrase_repo": Provide(lambda: phrase_repo, sync_to_thread=False),
        "long_phrase_repo": Provide(lambda: long_phrase_repo, sync_to_thread=False),
        "proposal_repo": Provide(lambda: proposal_repo, sync_to_thread=False),
        "long_proposal_repo": Provide(lambda: long_proposal_repo, sync_to_thread=False),
        "user_repo": Provide(lambda: user_repo, sync_to_thread=False),
        "chat_repo": Provide(lambda: chat_repo, sync_to_thread=False),
        "inline_user_repo": Provide(lambda: inline_user_repo, sync_to_thread=False),
    },
    middleware=[CookieBackendConfig(secret=config.session_secret.encode()).middleware],
    template_config=TemplateConfig(
        directory="src/templates", engine=JinjaTemplateEngine
    ),  # type: ignore[arg-type]
    request_class=HTMXRequest,
    before_request=auto_login_local,
    debug=not config.is_gae,
)

if app.template_engine:
    app.template_engine.engine.globals["apelativo"] = apelativo

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=config.port, reload=not config.is_gae)
