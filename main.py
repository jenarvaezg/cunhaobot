# [START gae_python37_app]
import logging
import os

from flask import Flask, request
from telegram import Update
from telegram.ext import Updater, Dispatcher

from handlers import error_handler, handlers, handle_ping as handle_telegram_ping

# Enable logging
logging.basicConfig(format='%(message)s',
                    level=logging.INFO)

logger = logging.getLogger('cunhaobot')
TG_TOKEN = os.environ["TG_TOKEN"]
BASE_URL = os.environ["BASE_URL"]
PORT = os.environ.get("PORT")


def tg_dispatcher() -> Dispatcher:
    # Create the Updater and pass it your bot's token.
    updater = Updater(TG_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    for handler in handlers:
        dp.add_handler(handler)

    # log all errors
    dp.add_error_handler(error_handler)

    return dp


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


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='0.0.0.0', port=PORT, debug=True)

# [END gae_python37_app]
