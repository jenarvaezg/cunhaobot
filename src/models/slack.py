from datetime import datetime
from typing import ClassVar
from pydantic import BaseModel, Field


class SlackInstallation(BaseModel):
    app_id: str | None = None
    enterprise_id: str | None = None
    enterprise_name: str | None = None
    enterprise_url: str | None = None
    team_id: str | None = None
    team_name: str | None = None
    bot_token: str | None = None
    bot_id: str | None = None
    bot_user_id: str | None = None
    bot_scopes: list[str] | None = None
    bot_refresh_token: str | None = None
    bot_token_expires_at: datetime | None = None
    user_id: str
    user_token: str | None = None
    user_scopes: list[str] | None = None
    user_refresh_token: str | None = None
    user_token_expires_at: datetime | None = None
    incoming_webhook_url: str | None = None
    incoming_webhook_channel: str | None = None
    incoming_webhook_channel_id: str | None = None
    incoming_webhook_configuration_url: str | None = None
    is_enterprise_install: bool = False
    token_type: str | None = None
    installed_at: datetime = Field(default_factory=datetime.now)

    kind: ClassVar[str] = "SlackInstallation"


class SlackBot(BaseModel):
    app_id: str | None = None
    enterprise_id: str | None = None
    enterprise_name: str | None = None
    team_id: str | None = None
    team_name: str | None = None
    bot_token: str
    bot_id: str
    bot_user_id: str
    bot_scopes: list[str] | None = None
    bot_refresh_token: str | None = None
    bot_token_expires_at: datetime | None = None
    is_enterprise_install: bool = False
    installed_at: datetime = Field(default_factory=datetime.now)

    kind: ClassVar[str] = "SlackBot"
