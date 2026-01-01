from litestar.testing import TestClient
from main import app as litestar_app


def test_slack_oauth_flow_cookie_handling():
    with TestClient(app=litestar_app) as client:
        # 1. Start OAuth flow
        # Bolt returns 200 with an install page by default in some configs, or 302 redirect.
        response = client.get("/slack/auth", follow_redirects=False)

        assert response.status_code in [200, 302]
        assert "slack-app-oauth-state" in response.cookies
        state_cookie = response.cookies["slack-app-oauth-state"]
        assert state_cookie is not None

        # Get the state from the redirect URL to Slack
        if response.status_code == 302:
            location = response.headers["location"]
        else:
            # If 200, the state is usually in a link in the body
            import re

            match = re.search(r"state=([a-zA-Z0-9-]+)", response.text)
            assert match is not None
            state_from_url = match.group(1)
            location = response.text  # for the debug print if needed

        if response.status_code == 302:
            import urllib.parse

            parsed_url = urllib.parse.urlparse(location)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            state_from_url = query_params["state"][0]

        # 2. Simulate Slack redirecting back to our app
        # If we DON'T provide the cookie, it should fail (invalid_browser)
        response_fail = client.get(
            "/slack/auth/redirect",
            params={"code": "fake-code", "state": state_from_url},
            follow_redirects=False,
        )
        assert response_fail.status_code in [400, 401, 500]
        assert b"invalid_browser" in response_fail.content

        # If we DO provide the cookie, it should get past the "invalid_browser" check
        client.cookies.set("slack-app-oauth-state", state_cookie)
        
        # In the test client, we might need to manually ensure the Cookie header is set 
        # as our to_bolt_request relies on it.
        response_ok_state = client.get(
            "/slack/auth/redirect", 
            params={"code": "fake-code", "state": state_from_url},
            follow_redirects=False,
            # TestClient usually handles cookies automatically if they were set in previous request 
            # or manually via client.cookies.set
        )

        assert b"invalid_browser" not in response_ok_state.content
