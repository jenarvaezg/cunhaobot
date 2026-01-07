import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from slack.handlers.bolt_listeners import register_listeners, _register_slack_user


class AsyncWebClientMock(AsyncMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.users_info = AsyncMock(
            return_value={
                "ok": True,
                "user": {"real_name": "Paco Reals", "name": "paco"},
            }
        )
        self.views_publish = AsyncMock()
        self.reactions_add = AsyncMock()


@pytest.mark.asyncio
async def test_register_slack_user_variants():
    client = AsyncWebClientMock()
    with patch("slack.handlers.bolt_listeners.services") as mock_services:
        mock_services.user_service.update_or_create_slack_user = AsyncMock()

        # Command variant
        await _register_slack_user({"user_id": "U1", "user_name": "N1"}, client)

        # Action variant (dict user)
        await _register_slack_user(
            {"user": {"id": "U2", "name": "N2", "username": "un2"}}, client
        )

        # Action variant (str user)
        await _register_slack_user({"user": "U3"}, client)

        # Event variant
        await _register_slack_user({"event": {"user": "U4"}}, client)

        assert mock_services.user_service.update_or_create_slack_user.call_count == 4


@pytest.mark.asyncio
async def test_handle_link_logic():
    app = MagicMock()
    commands = {}
    app.command = lambda name: lambda fn: commands.update({name: fn}) or fn
    app.action = lambda name: lambda fn: fn
    app.event = lambda name: lambda fn: fn

    register_listeners(app)
    handler = commands["/link"]

    ack = AsyncMock()
    respond = AsyncMock()
    client = AsyncWebClientMock()

    with patch("slack.handlers.bolt_listeners.services") as mock_services:
        mock_services.user_service.update_or_create_slack_user = AsyncMock()
        mock_services.user_service.generate_link_token = AsyncMock(
            return_value="TOKEN123"
        )
        mock_services.user_service.complete_link = AsyncMock(return_value=True)

        # Case 1: No text (generate)
        await handler(ack, {"user_id": "U1"}, respond, client)
        mock_services.user_service.generate_link_token.assert_called_once()

        # Case 2: With text (complete)
        await handler(ack, {"user_id": "U1", "text": "CODE"}, respond, client)
        mock_services.user_service.complete_link.assert_called_once_with(
            "CODE", "U1", "slack"
        )


@pytest.mark.asyncio
async def test_handle_sticker_command_variants():
    app = MagicMock()
    commands = {}
    app.command = lambda name: lambda fn: commands.update({name: fn}) or fn
    app.action = lambda name: lambda fn: fn
    app.event = lambda name: lambda fn: fn

    register_listeners(app)
    handler = commands["/sticker"]

    ack = AsyncMock()
    respond = AsyncMock()
    client = AsyncWebClientMock()
    say = AsyncMock()

    with patch("slack.handlers.bolt_listeners.services") as mock_services:
        mock_services.user_service.update_or_create_slack_user = AsyncMock()
        mock_services.phrase_service.get_phrases = AsyncMock(return_value=[])
        mock_services.phrase_service.find_most_similar = AsyncMock(
            return_value=(MagicMock(text="similar"), 80)
        )
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])

        # Help case
        await handler(ack, {"text": "help", "user_id": "U1"}, respond, client, say)
        respond.assert_called()

        # Search case (similar found)
        await handler(ack, {"text": "test", "user_id": "U1"}, respond, client, say)
        assert mock_services.phrase_service.find_most_similar.called


@pytest.mark.asyncio
async def test_handle_phrase_action_sticker():
    app = MagicMock()
    actions = {}
    app.action = lambda name: lambda fn: actions.update({name: fn}) or fn
    app.command = lambda name: lambda fn: fn
    app.event = lambda name: lambda fn: fn

    register_listeners(app)
    handler = actions["phrase"]

    ack = AsyncMock()
    respond = AsyncMock()
    client = AsyncWebClientMock()
    say = AsyncMock()

    body = {
        "actions": [{"value": "send-sticker-frase"}],
        "user": {"id": "U1", "name": "paco"},
    }

    with patch("slack.handlers.bolt_listeners.services") as mock_services:
        mock_services.user_service.update_or_create_slack_user = AsyncMock()
        mock_services.phrase_service.get_phrases = AsyncMock(return_value=[])
        mock_services.usage_service.log_usage = AsyncMock(return_value=[])

        await handler(ack, body, respond, client, say)
        ack.assert_called_once()
        respond.assert_called_once()
        url = respond.call_args[1]["blocks"][0]["image_url"]
        assert "sticker.png" in url or "text.png" in url
