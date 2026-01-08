import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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
    slack_signing_secret: str
    mod_chat_id: str
    is_gae: bool
    gemini_api_key: str
    twitter_consumer_key: str
    twitter_consumer_secret: str
    twitter_access_token: str
    twitter_access_secret: str
    bucket_name: str
    allow_local_login: bool

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
            slack_signing_secret=os.environ.get("SLACK_SIGNING_SECRET", ""),
            mod_chat_id=os.environ.get("MOD_CHAT_ID", ""),
            is_gae=is_gae,
            gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
            twitter_consumer_key=os.environ.get("TWITTER_CONSUMER_KEY", ""),
            twitter_consumer_secret=os.environ.get("TWITTER_CONSUMER_KEY_SECRET", ""),
            twitter_access_token=os.environ.get("TWITTER_ACCESS_TOKEN", ""),
            twitter_access_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", ""),
            bucket_name=os.environ.get("BUCKET_NAME", "cunhaobot-assets"),
            allow_local_login=os.environ.get("ALLOW_LOCAL_LOGIN", "false").lower()
            == "true",
        )


config = Config.from_env()
