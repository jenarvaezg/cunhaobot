import logging
import os
import json

from flask import Flask
from telegram import Update
from telegram.ext import Updater, Dispatcher

from handlers import error_handler, handlers

# Enable logging
logging.basicConfig(format='%(message)s',
                    level=logging.INFO)

logger = logging.getLogger('cunhaobot')
TG_TOKEN = os.environ["TG_TOKEN"]
BASE_URL = os.environ["BASE_URL"]
PORT = os.environ["PORT"]


def tg_dispatcher() -> Dispatcher:
    logger.info("STARTING MAIN")
    # Create the Updater and pass it your bot's token.
    updater = Updater(TG_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    for handler in handlers:
        dp.add_handler(handler)

    # log all errors
    dp.add_error_handler(error_handler)

    # Start the Bot
    # updater.bot.set_webhook(f'{BASE_URL}:{PORT}/{TG_TOKEN}')
    print(f'{BASE_URL}/{TG_TOKEN}')

    return dp


app = Flask(__name__)

# Not pretty, but I needed some sort of http server to work in appengine standard
@app.route('/')
def ping(self):
    return "I am alive"

#class TelegramHandler(webapp2.RequestHandler):
#    def post(self):
#        dispatcher = tg_dispatcher()
#        update = Update.de_json(json.loads(self.request.body), dispatcher.bot)
#        dispatcher.process_update(update)


print("SETTING APP")


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='0.0.0.0', port=8080, debug=True)
