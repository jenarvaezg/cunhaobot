import json
from typing import Annotated
import requests
from litestar import Controller, Request, get, post, Response
from litestar.response import Redirect
from litestar.params import Dependency
from slack.handlers import handle_slack
from services.phrase_service import PhraseService
from core.config import config


class SlackController(Controller):
    path = "/slack"

    @post("/", status_code=200)
    async def handler(
        self, request: Request, phrase_service: Annotated[PhraseService, Dependency()]
    ) -> Response:
        # Check content type to parse appropriately
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data_dict = await request.json()
            data_payload = data_dict
        else:
            data = await request.form()
            data_dict = dict(data)
            data_payload = data_dict
            if "payload" in data_dict:
                data_payload = json.loads(str(data_dict["payload"]))

        # Pass service to handler
        response = handle_slack(
            slack_data=data_payload,
            phrase_service=phrase_service,
        )

        if not response:
            return Response("", status_code=200)

        if "response_url" in data_payload:
            requests.post(
                data_payload["response_url"], json=response["indirect"], timeout=10
            )

        return Response(response["direct"], status_code=200)

    @get("/auth", sync_to_thread=False)
    def auth_handler(self) -> Redirect:
        scopes = [
            "commands",
            "chat:write",
            "chat:write.public",
            "chat:write.customize",
            "files:write",
        ]
        redirect_uri = f"{config.base_url}/slack/auth/redirect"
        auth_url = (
            "https://slack.com/oauth/v2/authorize"
            f"?client_id={config.slack_client_id}"
            f"&scope={','.join(scopes)}"
            f"&redirect_uri={redirect_uri}"
        )
        return Redirect(path=auth_url, status_code=302)

    @get("/auth/redirect")
    async def auth_redirect_handler(self, request: Request) -> str:
        import logging

        logger = logging.getLogger(__name__)

        code = request.query_params.get("code")
        if not code:
            logger.error("No code received in Slack redirect")
            return "Error: No code received"

        request_body = {
            "code": code,
            "redirect_uri": f"{config.base_url}/slack/auth/redirect",
        }

        logger.info(
            f"Exchanging Slack code for access token using Client ID: {config.slack_client_id[:5]}..."
        )
        response = requests.post(
            "https://slack.com/api/oauth.v2.access",
            data=request_body,
            auth=(config.slack_client_id, config.slack_client_secret),
            timeout=10,
        )
        resp_data = response.json()
        if not resp_data.get("ok"):
            logger.error(f"Slack OAuth error: {resp_data}")
            return f"Error during installation: {resp_data.get('error')}"

        # Here is where the bot token is!
        # resp_data['access_token'] is the xoxb- token
        logger.info(
            f"Slack installation successful for team: {resp_data.get('team', {}).get('name')}"
        )
        logger.info(f"Bot User ID: {resp_data.get('bot_user_id')}")
        # Log the token (be careful in production, but here we need to see it to configure it)
        logger.info(f"ACCESS_TOKEN: {resp_data.get('access_token')}")

        return "¡Instalación completada con éxito! Ya puedes cerrar esta ventana."
