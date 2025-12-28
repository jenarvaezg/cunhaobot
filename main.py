# [START gae_python39_app]
import json
import logging
import os

import requests
import tweepy
from flask import Flask, redirect, request
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

app = Flask(__name__)


@app.route("/")
def ping():
    return "I am alive"


@app.route(f"/{TG_TOKEN}", methods=["POST"])
async def telegram_handler():
    application = get_tg_application()
    await application.initialize()

    update = Update.de_json(request.json, application.bot)
    await application.process_update(update)
    return "Handled"


@app.route(f"/{TG_TOKEN}/ping", methods=["GET"])
async def telegram_ping_handler():
    application = get_tg_application()
    await application.initialize()

    await handle_telegram_ping(application.bot)
    return "OK"


@app.route("/slack", methods=["POST"])
def slack_handler():
    data = request.form
    if "payload" in data:
        data = json.loads(data["payload"])
    response = handle_slack(data)
    if response:
        response_url = data["response_url"]
        requests.post(response_url, json=response["indirect"])
        return response["direct"]

    return ""


@app.route("/slack/auth", methods=["GET"])
def slack_auth_handler():
    client_id = os.environ["SLACK_CLIENT_ID"]
    scopes = ["commands", "chat:write", "chat:write.public"]

    return redirect(
        f"https://slack.com/oauth/v2/authorize?client_id={client_id}&scope={','.join(scopes)}"
    )


@app.route("/slack/auth/redirect", methods=["GET"])
def slack_auth_redirect_handler():
    code = request.args.get("code")

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


@app.route("/twitter/auth/redirect", methods=["GET"])
def twitter_auth_redirect_handler():
    return ":)"


@app.route("/twitter/ping", methods=["GET"])
def twitter_ping_handler():
    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_KEY_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )
    client.create_tweet(text=LongPhrase.get_random_phrase().text)

    return ""


if __name__ == "__main__":
    print(TG_TOKEN)
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host="0.0.0.0", port=PORT, debug=True)

# [END gae_python39_app]
