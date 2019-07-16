# [START gae_python37_app]
import logging
import os
import requests

from flask import Flask, request
from telegram import Update

from tg import tg_dispatcher
from tg.handlers import handle_ping as handle_telegram_ping

# Enable logging
from models.phrase import LongPhrase

logging.basicConfig(format='%(message)s',
                    level=logging.INFO)

logger = logging.getLogger('cunhaobot')
TG_TOKEN = os.environ["TG_TOKEN"]
BASE_URL = os.environ["BASE_URL"]
PORT = os.environ.get("PORT")

app = Flask(__name__)


@app.route('/')
def ping():
    return "I am alive"


@app.route(f'/{TG_TOKEN}', methods=['POST'])
def telegram_handler():
    dispatcher = tg_dispatcher()
    update = Update.de_json(request.json, dispatcher.bot)
    dispatcher.process_update(update)
    return "Handled"


@app.route(f'/{TG_TOKEN}/ping', methods=['GET'])
def telegram_ping_handler():
    dispatcher = tg_dispatcher()
    handle_telegram_ping(dispatcher.bot)
    return "OK"


@app.route(f'/slack/frase', methods=['POST'])
def slack_phrase_handler():
    data = request.form
    text = data['text']
    response_url = data['response_url']
    requests.post(response_url, json={
        'text': LongPhrase.get_random_phrase(search=text).text,
        'response_type': 'in_channel',
    })

    return ""


if __name__ == '__main__':
    print(TG_TOKEN)
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='0.0.0.0', port=PORT, debug=True)

# [END gae_python37_app]
