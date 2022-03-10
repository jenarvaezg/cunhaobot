# [START gae_python39_app]
import logging
import os
import requests
import json

from flask import Flask, request, redirect
from telegram import Update

from slack.handlers import handle_slack
from slack.auth import do_auth as slack_do_auth

from tg import tg_dispatcher
from tg.handlers import handle_ping as handle_telegram_ping

# Enable logging
logging.basicConfig(format="%(message)s", level=logging.INFO)

TG_TOKEN = os.environ["TG_TOKEN"]
BASE_URL = os.environ["BASE_URL"]
PORT = os.environ.get("PORT")

app = Flask(__name__)


@app.route("/")
def ping():
    return "I am alive"


@app.route(f"/{TG_TOKEN}", methods=["POST"])
def telegram_handler():
    dispatcher = tg_dispatcher()
    update = Update.de_json(request.json, dispatcher.bot)
    dispatcher.process_update(update)
    return "Handled"


@app.route(f"/{TG_TOKEN}/ping", methods=["GET"])
def telegram_ping_handler():
    dispatcher = tg_dispatcher()
    handle_telegram_ping(dispatcher.bot)
    return "OK"


@app.route(f"/slack", methods=["POST"])
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


@app.route(f"/slack/auth", methods=["GET"])
def slack_auth_handler():
    client_id = os.environ["SLACK_CLIENT_ID"]
    scopes = ["commands", "chat:write", "chat:write.public"]

    return redirect(
        f'https://slack.com/oauth/v2/authorize?client_id={client_id}&scope={",".join(scopes)}'
    )


@app.route(f"/slack/auth/redirect", methods=["GET"])
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


if __name__ == "__main__":
    print(TG_TOKEN)
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host="0.0.0.0", port=PORT, debug=True)

# [END gae_python39_app]
