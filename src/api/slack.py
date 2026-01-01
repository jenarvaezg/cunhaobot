import logging
from typing import Annotated, Any

from litestar import Controller, Request, Response, get, post
from litestar.params import Dependency
from slack_bolt.async_app import AsyncBoltRequest
from slack_bolt.response import BoltResponse

from services.phrase_service import PhraseService
from slack.app import app

logger = logging.getLogger(__name__)


async def to_bolt_request(request: Request) -> AsyncBoltRequest:
    body = await request.body()
    headers = dict(request.headers)
    if "cookie" not in headers and "Cookie" not in headers and request.cookies:
        # Reconstruct cookie header if Litestar consumed it
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in request.cookies.items())

    logger.debug(f"Bolt Request Headers: {headers}")
    logger.debug(f"Request Cookies: {request.cookies}")

    return AsyncBoltRequest(
        body=body.decode("utf-8"),
        query=dict(request.query_params),
        headers=headers,
    )


def to_litestar_response(bolt_resp: BoltResponse) -> Response:
    logger.debug(f"Bolt Response Status: {bolt_resp.status}")
    logger.debug(f"Bolt Response Headers: {bolt_resp.headers}")

    resp = Response(
        content=bolt_resp.body,
        status_code=bolt_resp.status,
    )

    for k, v in bolt_resp.headers.items():
        if k.lower() == "set-cookie":
            values = v if isinstance(v, list) else [v]
            for cookie_str in values:
                if not isinstance(cookie_str, str):
                    continue
                # Basic parsing of Set-Cookie string to use resp.set_cookie
                # A full parser would be better, but for Slack Bolt state cookie it's usually simple.
                parts = cookie_str.split(";")
                if not parts:
                    continue
                name_value = parts[0].split("=", 1)
                if len(name_value) != 2:
                    continue
                name = name_value[0].strip()
                value = name_value[1].strip()

                extras: dict[str, Any] = {
                    "httponly": True,
                    "secure": True,
                    "samesite": "none",  # Changed to none for cross-site compatibility if needed
                }
                for part in parts[1:]:
                    part = part.strip().lower()
                    if part == "httponly":
                        extras["httponly"] = True
                    elif part == "secure":
                        extras["secure"] = True
                    elif part.startswith("path="):
                        extras["path"] = part[5:]
                    elif part.startswith("domain="):
                        extras["domain"] = part[7:]
                    elif part.startswith("samesite="):
                        # If bolt provides it, we can keep it, but we forced 'none' above
                        extras["samesite"] = part[9:]

                logger.debug(f"Setting cookie: {name}={value} with {extras}")
                resp.set_cookie(key=name, value=value, **extras)
        else:
            resp.headers[k] = v[0] if isinstance(v, list) else v

    return resp


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
