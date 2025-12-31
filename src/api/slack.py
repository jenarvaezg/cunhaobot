import logging
from typing import Annotated

from litestar import Controller, Request, Response, get, post
from litestar.params import Dependency
from slack_bolt.async_app import AsyncBoltRequest
from slack_bolt.response import BoltResponse

from services.phrase_service import PhraseService
from slack.app import app

logger = logging.getLogger(__name__)


async def to_bolt_request(request: Request) -> AsyncBoltRequest:
    body = await request.body()
    headers = request.headers
    return AsyncBoltRequest(
        body=body.decode("utf-8"),
        query=dict(request.query_params),
        headers={
            "X-Slack-Signature": headers.get("x-slack-signature", ""),
            "X-Slack-Request-Timestamp": headers.get("x-slack-request-timestamp", ""),
            "Content-Type": headers.get("content-type", ""),
        },
    )


def to_litestar_response(bolt_resp: BoltResponse) -> Response:
    headers: dict[str, str] = {}
    for k, v in bolt_resp.headers.items():
        if isinstance(v, list):
            headers[k] = v[0] if v else ""
        else:
            headers[k] = str(v)

    return Response(
        content=bolt_resp.body,
        status_code=bolt_resp.status,
        headers=headers,
    )


class SlackController(Controller):
    path = "/slack"

    @post("/", status_code=200)
    async def slack_events(
        self, request: Request, phrase_service: Annotated[PhraseService, Dependency()]
    ) -> Response:
        bolt_req: AsyncBoltRequest = await to_bolt_request(request)
        bolt_resp: BoltResponse = await app.async_dispatch(bolt_req)
        return to_litestar_response(bolt_resp)

    @get("/auth")
    async def auth(self, request: Request) -> Response:
        if app.oauth_flow is None:
            return Response("OAuth not configured", status_code=500)

        bolt_req: AsyncBoltRequest = await to_bolt_request(request)
        bolt_resp: BoltResponse = await app.oauth_flow.handle_installation(bolt_req)
        return to_litestar_response(bolt_resp)

    @get("/auth/redirect")
    async def auth_redirect(self, request: Request) -> Response:
        if app.oauth_flow is None:
            return Response("OAuth not configured", status_code=500)

        bolt_req: AsyncBoltRequest = await to_bolt_request(request)
        bolt_resp: BoltResponse = await app.oauth_flow.handle_callback(bolt_req)
        return to_litestar_response(bolt_resp)
