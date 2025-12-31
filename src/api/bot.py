from typing import Annotated
from litestar import Controller, Request, get, post
from litestar.params import Dependency
from telegram import Update
import tweepy
from tg import get_tg_application
from tg.handlers import handle_ping as handle_telegram_ping
from services.phrase_service import PhraseService
from core.config import config


class BotController(Controller):
    @post(path=f"/{config.tg_token}", status_code=200)
    async def telegram_handler(self, request: Request) -> str:
        application = get_tg_application()
        await application.initialize()
        if not application.bot.username:
            await application.bot.get_me()
        body = await request.json()
        update = Update.de_json(body, application.bot)
        await application.process_update(update)
        return "Handled"

    @get(path=f"/{config.tg_token}/ping")
    async def telegram_ping_handler(self) -> str:
        application = get_tg_application()
        await application.initialize()
        await handle_telegram_ping(application.bot)
        return "OK"

    @get("/twitter/ping", sync_to_thread=False)
    def twitter_ping_handler(
        self, phrase_service: Annotated[PhraseService, Dependency()]
    ) -> str:
        client = tweepy.Client(
            consumer_key=config.twitter_consumer_key,
            consumer_secret=config.twitter_consumer_secret,
            access_token=config.twitter_access_token,
            access_token_secret=config.twitter_access_secret,
        )
        phrase = phrase_service.get_random(long=True)
        client.create_tweet(text=phrase.text)
        return ""
