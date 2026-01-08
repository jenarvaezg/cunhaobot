import logging
from typing import Annotated
from litestar import Litestar, Request, get
from litestar.response import Redirect
from litestar.template.config import TemplateConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.static_files import create_static_files_router
from litestar.params import Dependency

from core.config import config
from core.di import dependencies
from api import WebController, AdminController, GameController
from api.slack import SlackController
from api.bot import BotController
from api.utils import get_proposals_context
from services import UserService
from utils import verify_telegram_auth
from utils.ui import apelativo
from infrastructure.protocols import ProposalRepository, LongProposalRepository

# Enable logging
logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


@get("/auth/telegram")
async def auth_telegram(
    request: Request,
    user_service: Annotated[UserService, Dependency()],
) -> Redirect:
    if not verify_telegram_auth(dict(request.query_params), config.tg_token):
        return Redirect(path="/")

    user_data = dict(request.query_params)
    user_id = user_data.get("id")
    first_name = user_data.get("first_name", "Usuario Web")
    username = user_data.get("username")

    if user_id:
        # Convert to int for Telegram consistency
        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)

        await user_service.update_user_data(
            user_id=user_id,
            name=first_name,
            username=username,
            platform="telegram",
        )

    request.set_session(
        {
            "user": {
                "id": user_id,
                "first_name": first_name,
                "username": username,
                "photo_url": user_data.get("photo_url"),
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


@get("/favicon.ico")
async def favicon_redirect() -> Redirect:
    return Redirect(path="/static/favicon.png")


def auto_login_local(request: Request) -> None:
    if not config.allow_local_login or config.is_gae or request.session.get("user"):
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
        GameController,
        SlackController,
        BotController,
        auth_telegram,
        logout,
        proposals_search,
        ping,
        create_static_files_router(directories=["src/static"], path="/static"),
    ],
    dependencies=dependencies,
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
