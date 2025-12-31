import logging
from typing import Annotated

from litestar import Controller, Request, Response, get, post
from litestar.params import Dependency
from slack_bolt.async_app import AsyncBoltRequest

from services.phrase_service import PhraseService
from slack.app import app

logger = logging.getLogger(__name__)


async def to_bolt_request(request: Request) -> AsyncBoltRequest:
    return AsyncBoltRequest(
        body=(await request.body()).decode("utf-8"),
        query=dict(request.query_params),
        headers=dict(request.headers),
    )


def to_litestar_response(bolt_resp) -> Response:
    headers = {}
    for k, v in bolt_resp.headers.items():
        if isinstance(v, list):
            # For Set-Cookie we might need multiple headers,
            # but Litestar's Response constructor takes a dict.
            # To support multiple headers with the same key, we'd need to use a different approach.
            # For now, let's take the first one to avoid the crash.
            headers[k] = v[0] if v else ""
        else:
            headers[k] = v

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
        bolt_req = await to_bolt_request(request)
        bolt_resp = await app.async_dispatch(bolt_req)
        return to_litestar_response(bolt_resp)

    @get("/auth")
    async def auth(self, request: Request) -> Response:
        if app.oauth_flow is None:
            return Response("OAuth not configured", status_code=500)

        bolt_req = await to_bolt_request(request)
        bolt_resp = await app.oauth_flow.handle_installation(bolt_req)
        return to_litestar_response(bolt_resp)

    @get("/auth/redirect")
    async def auth_redirect(self, request: Request) -> Response:
        if app.oauth_flow is None:
            return Response("OAuth not configured", status_code=500)

        bolt_req = await to_bolt_request(request)
        bolt_resp = await app.oauth_flow.handle_callback(bolt_req)
        return to_litestar_response(bolt_resp)
