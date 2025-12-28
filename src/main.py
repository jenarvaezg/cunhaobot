import json
import logging
import os

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

from models.phrase import LongPhrase, Phrase
from models.proposal import LongProposal, Proposal
from slack.handlers import handle_slack
from tg import get_tg_application
from tg.handlers import handle_ping as handle_telegram_ping
from utils import normalize_str, verify_telegram_auth

# Enable logging
logging.basicConfig(format="%(message)s", level=logging.INFO)

TG_TOKEN = os.environ["TG_TOKEN"]
BASE_URL = os.environ["BASE_URL"]
PORT = int(os.environ.get("PORT", 5050))
SESSION_SECRET = os.environ.get("SESSION_SECRET", "a-very-secret-key-of-32-chars-!!")


@get("/", sync_to_thread=False)
def index(request: Request) -> Template:
    short_phrases = Phrase.get_phrases()
    long_phrases = LongPhrase.get_phrases()
    return Template(
        template_name="index.html",
        context={
            "short_phrases": sorted(
                short_phrases, key=lambda x: x.usages, reverse=True
            ),
            "long_phrases": sorted(long_phrases, key=lambda x: x.usages, reverse=True),
            "user": request.session.get("user"),
        },
    )


@get("/proposals", sync_to_thread=False)
def proposals(request: Request) -> Template:
    # Get all filters from query params
    filters = {k: v for k, v in request.query_params.items() if k not in ["search"]}
    search_query = request.query_params.get("search", "")

    all_short_proposals = Proposal.get_proposals(search=search_query, **filters)
    all_long_proposals = LongProposal.get_proposals(search=search_query, **filters)

    short_phrases_texts = {normalize_str(p.text) for p in Phrase.get_phrases()}
    long_phrases_texts = {normalize_str(p.text) for p in LongPhrase.get_phrases()}

    pending_short = [
        p
        for p in all_short_proposals
        if normalize_str(p.text) not in short_phrases_texts
    ]
    pending_long = [
        p for p in all_long_proposals if normalize_str(p.text) not in long_phrases_texts
    ]

    return Template(
        template_name="proposals.html",
        context={
            "pending_short": pending_short,
            "pending_long": pending_long,
            "user": request.session.get("user"),
        },
    )


@get("/auth/telegram", sync_to_thread=False)
def auth_telegram(request: Request) -> Redirect:
    if verify_telegram_auth(dict(request.query_params), TG_TOKEN):
        # Store user info in session
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


@get("/logout", sync_to_thread=False)
def logout(request: Request) -> Redirect:
    request.clear_session()
    return Redirect(path="/")


@get("/proposals/search", sync_to_thread=False)
def proposals_search(request: HTMXRequest) -> HTMXTemplate:
    filters = {k: v for k, v in request.query_params.items() if k not in ["search"]}

    search_query = request.query_params.get("search", "")

    all_short_proposals = Proposal.get_proposals(search=search_query, **filters)

    all_long_proposals = LongProposal.get_proposals(search=search_query, **filters)

    short_phrases_texts = {normalize_str(p.text) for p in Phrase.get_phrases()}

    long_phrases_texts = {normalize_str(p.text) for p in LongPhrase.get_phrases()}

    pending_short = [
        p
        for p in all_short_proposals
        if normalize_str(p.text) not in short_phrases_texts
    ]

    pending_long = [
        p for p in all_long_proposals if normalize_str(p.text) not in long_phrases_texts
    ]

    return HTMXTemplate(
        template_name="partials/proposals_list.html",
        context={
            "pending_short": pending_short,
            "pending_long": pending_long,
        },
    )


@get("/search", sync_to_thread=False)
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


@get("/ping", sync_to_thread=False)
def ping() -> str:
    return "I am alive"


@post(path=f"/{TG_TOKEN}", status_code=200)
async def telegram_handler(request: Request) -> str:
    application = get_tg_application()
    await application.initialize()

    body = await request.json()
    update = Update.de_json(body, application.bot)
    await application.process_update(update)
    return "Handled"


@get(path=f"/{TG_TOKEN}/ping")
async def telegram_ping_handler() -> str:
    application = get_tg_application()
    await application.initialize()

    await handle_telegram_ping(application.bot)
    return "OK"


@post(path="/slack", status_code=200)
async def slack_handler(request: Request) -> Response[str]:
    data = await request.form()
    data_dict = dict(data)

    if "payload" in data_dict:
        data_payload = json.loads(str(data_dict["payload"]))
    else:
        data_payload = data_dict

    response = handle_slack(data_payload)
    if not response:
        return Response("", status_code=200)

    requests.post(data_payload["response_url"], json=response["indirect"])
    return Response(response["direct"], status_code=200)


@get("/slack/auth", sync_to_thread=False)
def slack_auth_handler() -> Redirect:
    client_id = os.environ["SLACK_CLIENT_ID"]
    scopes = ["commands", "chat:write", "chat:write.public"]

    return Redirect(
        path=f"https://slack.com/oauth/v2/authorize?client_id={client_id}&scope={','.join(scopes)}",
        status_code=302,
    )


@get("/slack/auth/redirect")
async def slack_auth_redirect_handler(request: Request) -> str:
    code = request.query_params.get("code")

    request_body = {
        "code": code,
        "client_id": os.environ["SLACK_CLIENT_ID"],
        "client_secret": os.environ["SLACK_CLIENT_SECRET"],
    }

    requests.post(
        "https://slack.com/api/oauth.v2.access",
        request_body,
    )  # We dont want the token

    return ":)"


@get("/twitter/auth/redirect", sync_to_thread=False)
def twitter_auth_redirect_handler() -> str:
    return ":)"


@get("/twitter/ping", sync_to_thread=False)
def twitter_ping_handler() -> str:
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
    middleware=[
        CookieBackendConfig(secret=SESSION_SECRET.encode()).middleware,
    ],
    template_config=TemplateConfig(
        directory="src/templates",
        engine=JinjaTemplateEngine,  # type: ignore[invalid-argument-type]
    ),
    request_class=HTMXRequest,
)

if __name__ == "__main__":
    import uvicorn

    print(TG_TOKEN)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
