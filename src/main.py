import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypedDict, cast, Any

import asyncio
import requests
import tweepy
from litestar import Litestar, Request, get, post
from litestar.response import Redirect, Response, Template
from litestar.template.config import TemplateConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.static_files import create_static_files_router
from telegram import Update
from telegram.error import BadRequest, TelegramError

from models.phrase import LongPhrase, Phrase
from models.proposal import LongProposal, Proposal, get_proposal_class_by_kind
from models.user import InlineUser, User
from slack.handlers import handle_slack
from tg import get_tg_application
from tg.handlers import handle_ping as handle_telegram_ping
from tg.handlers.utils.callback_query import approve_proposal, dismiss_proposal
from utils import verify_telegram_auth

# Enable logging
logging.basicConfig(format="%(message)s", level=logging.INFO)


class ConfigError(Exception):
    """Raised when required environment variables are missing."""


@dataclass
class Config:
    tg_token: str
    base_url: str
    port: int
    session_secret: str
    owner_id: str
    slack_client_id: str
    slack_client_secret: str
    mod_chat_id: str
    is_gae: bool

    @classmethod
    def from_env(cls) -> "Config":
        required = [
            "TG_TOKEN",
            "SLACK_CLIENT_ID",
            "SLACK_CLIENT_SECRET",
            "SESSION_SECRET",
            "OWNER_ID",
        ]
        missing = [var for var in required if var not in os.environ]
        is_gae = os.environ.get("GAE_ENV") == "standard"
        if missing and is_gae:
            raise ConfigError(f"Missing environment variables: {', '.join(missing)}")

        return cls(
            tg_token=os.environ.get("TG_TOKEN", "dummy_token"),
            base_url=os.environ.get("BASE_URL", "http://localhost:5050"),
            port=int(os.environ.get("PORT", 5050)),
            session_secret=os.environ.get(
                "SESSION_SECRET", "a-very-secret-key-of-32-chars-!!"
            ),
            owner_id=os.environ.get("OWNER_ID", ""),
            slack_client_id=os.environ.get("SLACK_CLIENT_ID", ""),
            slack_client_secret=os.environ.get("SLACK_CLIENT_SECRET", ""),
            mod_chat_id=os.environ.get("MOD_CHAT_ID", ""),
            is_gae=is_gae,
        )


config = Config.from_env()

# Global cache for curators to avoid hitting Telegram API limits
_CURATORS_CACHE: dict[int, str] = {}
_LAST_CURATORS_UPDATE: datetime | None = None


class ProposalsContext(TypedDict):
    pending_short: list[Proposal]
    pending_long: list[LongProposal]
    user: dict[str, str] | None
    owner_id: str


def get_proposals_context(request: Request) -> ProposalsContext:
    filters = {k: v for k, v in request.query_params.items() if k not in ["search"]}
    search_query = request.query_params.get("search", "")

    # Default to only showing active proposals
    if "voting_ended" not in filters:
        filters["voting_ended"] = False

    # Apply limit to avoid huge DOM rendering
    all_short = Proposal.get_proposals(search=search_query, limit=50, **filters)
    all_long = LongProposal.get_proposals(search=search_query, limit=50, **filters)

    user_session = cast(dict[str, str] | None, request.session.get("user"))
    return {
        "pending_short": all_short,
        "pending_long": all_long,
        "user": user_session,
        "owner_id": config.owner_id,
    }


@get("/", sync_to_thread=True)
def index(request: Request) -> Template:
    # Limit initial phrases to 50 top used ones
    short_phrases = Phrase.get_phrases(limit=50)
    long_phrases = LongPhrase.get_phrases(limit=50)

    return Template(
        template_name="index.html",
        context={
            "short_phrases": sorted(
                short_phrases, key=lambda x: x.usages, reverse=True
            ),
            "long_phrases": sorted(long_phrases, key=lambda x: x.usages, reverse=True),
            "user": request.session.get("user"),
            "owner_id": config.owner_id,
        },
    )


@get("/proposals", sync_to_thread=True)
def proposals(request: Request) -> Template:
    return Template(
        template_name="proposals.html",
        context=cast(dict[str, Any], get_proposals_context(request)),
    )


@get("/orphans")
async def orphans(request: Request) -> Template | Response:
    global _CURATORS_CACHE, _LAST_CURATORS_UPDATE
    user = request.session.get("user")
    if not user or str(user.get("id")) != str(config.owner_id):
        return Response("Unauthorized", status_code=401)

    orphan_short = [p for p in Phrase.get_phrases() if not p.proposal_id]
    orphan_long = [p for p in LongPhrase.get_phrases() if not p.proposal_id]
    all_proposals = Proposal.load_all()
    all_long_proposals = LongProposal.load_all()

    now = datetime.now()
    if not _LAST_CURATORS_UPDATE or (now - _LAST_CURATORS_UPDATE) > timedelta(
        minutes=10
    ):
        application = get_tg_application()
        await application.initialize()
        bot = application.bot
        new_cache = {}
        try:
            admins = await bot.get_chat_administrators(chat_id=config.mod_chat_id)
            for admin in admins:
                if not admin.user.is_bot:
                    new_cache[admin.user.id] = admin.user.name or admin.user.first_name

            active_ids = set()
            for p in all_proposals + all_long_proposals:
                active_ids.add(p.user_id)
                active_ids.update(p.liked_by)
                active_ids.update(p.disliked_by)

            ids_to_check = active_ids - set(new_cache.keys()) - {0}

            async def check_user(uid):
                try:
                    m = await bot.get_chat_member(
                        chat_id=config.mod_chat_id, user_id=uid
                    )
                    if m.status in ["member", "administrator", "creator"]:
                        return uid
                except (BadRequest, TelegramError):
                    pass
                return None

            check_tasks = [check_user(uid) for uid in list(ids_to_check)[:100]]
            member_ids = await asyncio.gather(*check_tasks)

            users_db = {u.chat_id: u.name for u in User.load_all() if not u.is_group}
            inline_db = {u.user_id: u.name for u in InlineUser.get_all()}
            db_names = {**users_db, **inline_db}

            for mid in member_ids:
                if mid and mid not in new_cache:
                    new_cache[mid] = db_names.get(mid, f"User {mid}")

            _CURATORS_CACHE = new_cache
            _LAST_CURATORS_UPDATE = now
        except Exception as e:
            logging.error(f"Error updating curators: {e}")

    sorted_known_users = sorted(
        [{"id": str(uid), "name": name} for uid, name in _CURATORS_CACHE.items()],
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
async def link_orphan_web(request: Request) -> Response[str]:
    user = request.session.get("user")
    if not user or str(user.get("id")) != str(config.owner_id):
        return Response("Unauthorized", status_code=401)
    data = await request.json()
    phrase_text, kind, proposal_id = (
        data.get("phrase_text"),
        data.get("kind"),
        data.get("proposal_id"),
    )
    if not all([phrase_text, kind, proposal_id]):
        return Response("Missing data", status_code=400)
    phrase_class = Phrase if kind == "Phrase" else LongPhrase
    repo = phrase_class.get_repository()
    phrase = next((p for p in repo.get_phrases() if p.text == phrase_text), None)
    if not phrase:
        return Response("Phrase not found", status_code=404)
    phrase.proposal_id = proposal_id
    repo.save(phrase)
    return Response("Linked", status_code=200)


@post("/orphans/manual-link")
async def manual_link_orphan_web(request: Request) -> Response[str]:
    user = request.session.get("user")
    if not user or str(user.get("id")) != str(config.owner_id):
        return Response("Unauthorized", status_code=401)
    data = await request.json()
    phrase_text = data.get("phrase_text")
    kind = data.get("kind")
    creator_id = data.get("creator_id")
    username = data.get("username")
    date_str = data.get("date")
    chat_id = data.get("chat_id", "0")

    if not all([phrase_text, kind, date_str]) or not (creator_id or username):
        return Response("Faltan datos (se requiere Autor o Username)", status_code=400)

    # 1. Resolve Creator ID if not provided directly
    final_creator_id = 0
    if creator_id:
        final_creator_id = int(creator_id)
    elif username:
        # Search in DB for this name/username
        clean_name = username.removeprefix("@").lower()
        users_db = User.load_all(ignore_gdpr=True)
        inline_db = InlineUser.get_all()

        # Exact match first, then partial
        found = None
        for u in users_db:
            if not u.is_group and clean_name in u.name.lower():
                found = u.chat_id
                break
        if not found:
            for iu in inline_db:
                if clean_name in iu.name.lower():
                    found = iu.user_id
                    break

        if not found:
            return Response(
                f"Usuario '{username}' no encontrado en la base de datos",
                status_code=404,
            )
        final_creator_id = found

    try:
        created_at = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return Response("Formato de fecha inválido", status_code=400)

    # 2. Update Phrase directly without creating a ghost proposal
    phrase_class = Phrase if kind == "Phrase" else LongPhrase
    repo = phrase_class.get_repository()
    phrase = next((p for p in repo.get_phrases() if p.text == phrase_text), None)

    if phrase:
        phrase.proposal_id = (
            ""  # Ensure it's explicitly empty for manually linked phrases
        )
        phrase.user_id = final_creator_id
        phrase.chat_id = int(chat_id)
        phrase.created_at = created_at
        repo.save(phrase)

    return Response("Linked", status_code=200)


async def _handle_proposal_web_action(
    request: Request, kind: str, proposal_id: str, action: str
) -> Response[str]:
    user = request.session.get("user")
    if not user or str(user.get("id")) != str(config.owner_id):
        return Response("Unauthorized", status_code=401)
    proposal_class = get_proposal_class_by_kind(kind)
    proposal = proposal_class.load(proposal_id)
    if not proposal:
        return Response("Proposal not found", status_code=404)
    application = get_tg_application()
    await application.initialize()
    if action == "approve":
        await approve_proposal(proposal, application.bot)
    else:
        await dismiss_proposal(proposal, application.bot)

    return Response(
        action.capitalize(), status_code=200, headers={"HX-Trigger": "refreshProposals"}
    )


@post("/proposals/{kind:str}/{proposal_id:str}/approve")
async def approve_proposal_web(
    request: Request, kind: str, proposal_id: str
) -> Response[str]:
    return await _handle_proposal_web_action(request, kind, proposal_id, "approve")


@post("/proposals/{kind:str}/{proposal_id:str}/reject")
async def reject_proposal_web(
    request: Request, kind: str, proposal_id: str
) -> Response[str]:
    return await _handle_proposal_web_action(request, kind, proposal_id, "reject")


@get("/auth/telegram", sync_to_thread=True)
def auth_telegram(request: Request) -> Redirect:
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


@get("/logout", sync_to_thread=True)
def logout(request: Request) -> Redirect:
    request.clear_session()
    return Redirect(path="/")


@get("/proposals/search", sync_to_thread=True)
def proposals_search(request: HTMXRequest) -> HTMXTemplate:
    return HTMXTemplate(
        template_name="partials/proposals_list.html",
        context=get_proposals_context(request),
    )


@get("/search", sync_to_thread=True)
def search(request: HTMXRequest) -> HTMXTemplate:
    filters = {k: v for k, v in request.query_params.items() if k not in ["search"]}
    search_query = request.query_params.get("search", "")
    short_phrases = Phrase.get_phrases(search=search_query, **filters)
    long_phrases = LongPhrase.get_phrases(search=search_query, **filters)
    return HTMXTemplate(
        template_name="partials/phrases_list.html",
        context={
            "short_phrases": sorted(
                short_phrases, key=lambda x: x.usages, reverse=True
            ),
            "long_phrases": sorted(long_phrases, key=lambda x: x.usages, reverse=True),
        },
    )


@get("/ping", sync_to_thread=True)
def ping() -> str:
    return "I am alive"


@post(path=f"/{config.tg_token}", status_code=200)
async def telegram_handler(request: Request) -> str:
    application = get_tg_application()
    await application.initialize()
    body = await request.json()
    update = Update.de_json(body, application.bot)
    await application.process_update(update)
    return "Handled"


@get(path=f"/{config.tg_token}/ping")
async def telegram_ping_handler() -> str:
    application = get_tg_application()
    await application.initialize()
    await handle_telegram_ping(application.bot)
    return "OK"


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


@post(path="/slack", status_code=200)
async def slack_handler(request: Request) -> Response[str]:  # pragma: no cover
    data = await request.form()
    data_dict = dict(data)
    data_payload = (
        json.loads(str(data_dict["payload"])) if "payload" in data_dict else data_dict
    )
    response = handle_slack(data_payload)
    if not response:
        return Response("", status_code=200)
    requests.post(
        data_payload["response_url"], json=response["indirect"]
    )  # pragma: no cover
    return Response(response["direct"], status_code=200)


@get("/slack/auth", sync_to_thread=False)
def slack_auth_handler() -> Redirect:
    scopes = ["commands", "chat:write", "chat:write.public"]
    return Redirect(
        path=f"https://slack.com/oauth/v2/authorize?client_id={config.slack_client_id}&scope={','.join(scopes)}",
        status_code=302,
    )


@get("/slack/auth/redirect")
async def slack_auth_redirect_handler(request: Request) -> str:
    code = request.query_params.get("code")
    request_body = {
        "code": code,
        "client_id": config.slack_client_id,
        "client_secret": config.slack_client_secret,
    }
    requests.post("https://slack.com/api/oauth.v2.access", request_body)
    return ":)"


@get("/twitter/auth/redirect", sync_to_thread=False)
def twitter_auth_redirect_handler() -> str:
    return ":)"


@get("/twitter/ping", sync_to_thread=False)
def twitter_ping_handler() -> str:  # pragma: no cover
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_KEY_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )
    client.create_tweet(text=LongPhrase.get_random_phrase().text)
    return ""


app = Litestar(
    route_handlers=[
        index,
        proposals,
        orphans,
        link_orphan_web,
        manual_link_orphan_web,
        approve_proposal_web,
        reject_proposal_web,
        auth_telegram,
        logout,
        proposals_search,
        search,
        ping,
        telegram_handler,
        telegram_ping_handler,
        slack_handler,
        slack_auth_handler,
        slack_auth_redirect_handler,
        twitter_auth_redirect_handler,
        twitter_ping_handler,
        create_static_files_router(directories=["src/static"], path="/static"),
    ],
    middleware=[CookieBackendConfig(secret=config.session_secret.encode()).middleware],
    template_config=TemplateConfig(
        directory="src/templates", engine=JinjaTemplateEngine
    ),  # type: ignore[invalid-argument-type]
    request_class=HTMXRequest,
    before_request=auto_login_local,
)

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    print(config.tg_token)
    uvicorn.run("main:app", host="0.0.0.0", port=config.port, reload=not config.is_gae)
