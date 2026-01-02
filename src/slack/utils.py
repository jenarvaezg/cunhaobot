import logging
from typing import TYPE_CHECKING, Callable, Awaitable
from slack_sdk.web.async_client import AsyncWebClient
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)

if TYPE_CHECKING:
    from services.badge_service import Badge

logger = logging.getLogger(__name__)


async def get_slack_history(
    client: AsyncWebClient,
    channel: str,
    bot_user_id: str,
    thread_ts: str | None = None,
    limit: int = 15,
) -> list[ModelMessage]:
    """
    Fetches the history in Slack using the Web API to build context for the AI agent.
    If thread_ts is provided, it fetches the thread replies.
    Otherwise, it fetches the general channel history.
    """
    try:
        if thread_ts:
            # Fetch thread replies
            response = await client.conversations_replies(
                channel=channel, ts=thread_ts, limit=limit + 1
            )
        else:
            # Fetch general channel history
            response = await client.conversations_history(
                channel=channel, limit=limit + 1
            )

        if not response.get("ok"):
            logger.warning(f"Slack API error fetching history: {response.get('error')}")
            return []

        messages = response.get("messages", [])
        if not messages:
            return []

        # We want context BEFORE the current message.
        # Usually the trigger message is the last one.
        context_messages = messages[:-1] if len(messages) > 0 else []

        # Ensure chronological order (conversations.history is newest first, replies is oldest first)
        if not thread_ts:
            context_messages.reverse()

        # Limit to requested number
        context_messages = context_messages[-limit:]

        history: list[ModelMessage] = []
        for msg in context_messages:
            user_id = msg.get("user")
            text = msg.get("text", "")

            if not text:
                continue

            if user_id == bot_user_id:
                history.append(ModelResponse(parts=[TextPart(content=text)]))
            else:
                history.append(
                    ModelRequest(
                        parts=[UserPromptPart(content=f"Usuario ({user_id}): {text}")]
                    )
                )

        return history
    except Exception as e:
        logger.exception(f"Error extracting Slack history: {e}")
        return []


async def notify_new_badges_slack(
    say: Callable[..., Awaitable[object]], new_badges: list["Badge"]
) -> None:
    """Sends a notification for each newly awarded badge in Slack."""
    if not new_badges:
        return

    from utils.ui import apelativo

    for badge in new_badges:
        try:
            a = apelativo()
            text = (
                f"🎊 *¡LOGRO DESBLOQUEADO, {a.upper()}!* 🎊\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{badge.icon} *{badge.name}*\n"
                f"_{badge.description}_"
            )
            await say(text=text)
        except Exception as e:
            logger.error(f"Error notifying badge {badge.id} in Slack: {e}")
