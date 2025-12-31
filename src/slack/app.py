import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings

from core.config import config
from infrastructure.datastore.slack_store import (
    DatastoreInstallationStore,
    DatastoreOAuthStateStore,
)
from slack.handlers.bolt_listeners import register_listeners

logger = logging.getLogger(__name__)

# Initialize the stores
installation_store = DatastoreInstallationStore()
state_store = DatastoreOAuthStateStore()

# Initialize OAuth settings
oauth_settings = AsyncOAuthSettings(
    client_id=config.slack_client_id,
    client_secret=config.slack_client_secret,
    scopes=[
        "commands",
        "chat:write",
        "chat:write.public",
        "chat:write.customize",
    ],
    installation_store=installation_store,
    state_store=state_store,
    install_path="/slack/auth",
    redirect_uri_path="/slack/auth/redirect",
)

# Initialize the Bolt App
app = AsyncApp(
    signing_secret=config.slack_signing_secret,
    oauth_settings=oauth_settings,
)

# Register listeners
register_listeners(app)


# You can add global middlewares here if needed
@app.middleware
async def log_request(logger, body, next):
    logger.debug(f"Request body: {body}")
    return await next()
