import os
import pytest
from unittest.mock import patch
from core.config import Config, ConfigError


def test_config_from_env_gae_missing_required():
    # Simulate GAE environment and missing required variables
    with patch.dict(
        os.environ,
        {
            "GAE_ENV": "standard",
            "TG_TOKEN": "dummy_token",
            "SLACK_CLIENT_ID": "dummy_id",  # This will be deleted
            "SLACK_CLIENT_SECRET": "dummy_secret",
            "SESSION_SECRET": "dummy_session_secret_32_chars_long!",
            "OWNER_ID": "dummy_owner_id",
            "MOD_CHAT_ID": "dummy_mod_chat_id",
            "GEMINI_API_KEY": "dummy_gemini_key",
            "TWITTER_CONSUMER_KEY": "dummy_twitter_consumer_key",
            "TWITTER_CONSUMER_KEY_SECRET": "dummy_twitter_consumer_secret",
            "TWITTER_ACCESS_TOKEN": "dummy_twitter_access_token",
            "TWITTER_ACCESS_TOKEN_SECRET": "dummy_twitter_access_token_secret",
        },
        clear=True,
    ):
        del os.environ["SLACK_CLIENT_ID"]  # Missing this one
        with pytest.raises(ConfigError) as excinfo:
            Config.from_env()
        assert "Missing environment variables: SLACK_CLIENT_ID" in str(excinfo.value)


def test_config_from_env_local():
    # Simulate local environment (GAE_ENV not 'standard')
    with patch.dict(os.environ, {}, clear=True):
        # Provide some dummy values for required fields
        os.environ["TG_TOKEN"] = "test_tg_token"
        os.environ["SLACK_CLIENT_ID"] = "test_slack_id"
        os.environ["SLACK_CLIENT_SECRET"] = "test_slack_secret"
        os.environ["SESSION_SECRET"] = "test_session_secret_32_chars_long!"
        os.environ["OWNER_ID"] = "test_owner_id"
        os.environ["GAE_ENV"] = "development"  # Not 'standard'

        config = Config.from_env()
        assert config.tg_token == "test_tg_token"
        assert config.slack_client_id == "test_slack_id"
        assert not config.is_gae


def test_config_allow_local_login():
    with patch.dict(os.environ, {"ALLOW_LOCAL_LOGIN": "true"}, clear=True):
        config = Config.from_env()
        assert config.allow_local_login is True

    with patch.dict(os.environ, {"ALLOW_LOCAL_LOGIN": "false"}, clear=True):
        config = Config.from_env()
        assert config.allow_local_login is False

    with patch.dict(os.environ, {}, clear=True):
        config = Config.from_env()
        assert config.allow_local_login is False  # Default to False


def test_config_from_env_gae_all_required():
    # Simulate GAE environment and all required variables present
    with patch.dict(os.environ, {}, clear=True):
        os.environ["TG_TOKEN"] = "gae_tg_token"
        os.environ["SLACK_CLIENT_ID"] = "gae_slack_id"
        os.environ["SLACK_CLIENT_SECRET"] = "gae_slack_secret"
        os.environ["SESSION_SECRET"] = "gae_session_secret_32_chars_long!"
        os.environ["OWNER_ID"] = "gae_owner_id"
        os.environ["MOD_CHAT_ID"] = "gae_mod_chat_id"
        os.environ["GAE_ENV"] = "standard"
        os.environ["GEMINI_API_KEY"] = "gae_gemini_key"
        os.environ["TWITTER_CONSUMER_KEY"] = "gae_twitter_consumer_key"
        os.environ["TWITTER_CONSUMER_KEY_SECRET"] = "gae_twitter_consumer_secret"
        os.environ["TWITTER_ACCESS_TOKEN"] = "gae_twitter_access_token"
        os.environ["TWITTER_ACCESS_TOKEN_SECRET"] = "gae_twitter_access_token_secret"

        config = Config.from_env()
        assert config.tg_token == "gae_tg_token"
        assert config.is_gae
        assert config.gemini_api_key == "gae_gemini_key"
        assert config.twitter_consumer_key == "gae_twitter_consumer_key"
        assert config.twitter_consumer_secret == "gae_twitter_consumer_secret"
