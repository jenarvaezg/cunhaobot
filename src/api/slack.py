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
        auth_url = (
            "https://slack.com/oauth/v2/authorize"
            f"?client_id={config.slack_client_id}"
            f"&scope={','.join(scopes)}"
        )
        return Redirect(path=auth_url, status_code=302)

    @get("/auth/redirect")
    async def auth_redirect_handler(self, request: Request) -> str:
        code = request.query_params.get("code")
        request_body = {
            "code": code,
            "client_id": config.slack_client_id,
            "client_secret": config.slack_client_secret,
        }
        # Consider moving this to a dedicated Slack service later
        requests.post(
            "https://slack.com/api/oauth.v2.access", data=request_body, timeout=10
        )
        return ":)"
