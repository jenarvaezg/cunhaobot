import json
import logging
import os

import requests
import tweepy
from litestar import Litestar, Request, get, post
from litestar.response import Redirect, Response
from telegram import Update

from models.phrase import LongPhrase
from slack.handlers import handle_slack
from tg import get_tg_application
from tg.handlers import handle_ping as handle_telegram_ping

# Enable logging
logging.basicConfig(format="%(message)s", level=logging.INFO)

TG_TOKEN = os.environ["TG_TOKEN"]
BASE_URL = os.environ["BASE_URL"]
PORT = int(os.environ.get("PORT", 5050))


@get("/", sync_to_thread=False)
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
        ping,
        telegram_handler,
        telegram_ping_handler,
        slack_handler,
        slack_auth_handler,
        slack_auth_redirect_handler,
        twitter_auth_redirect_handler,
        twitter_ping_handler,
    ]
)

if __name__ == "__main__":
    import uvicorn

    print(TG_TOKEN)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
