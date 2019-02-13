import logging
import os

import webapp2
from telegram.ext import Updater

from handlers import error_handler, handlers

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger('cunhaobot')
TG_TOKEN = os.environ["TG_TOKEN"]


def main():
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
    logger.info("STARTING POLLING")
    updater.start_polling()

    logger.info("STARTED POLLING")
    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    # updater.idle()


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')


main()
app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
