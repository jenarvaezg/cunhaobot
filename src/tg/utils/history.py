from telegram import Message
from telegram.ext import CallbackContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)


async def record_message_in_history(message: Message, context: CallbackContext) -> None:
    """
    Records a message in the chat_data history.
    """
    if not message or not message.text or context.chat_data is None:
        return

    history = context.chat_data.get("history", [])

    # Avoid duplicates (e.g. if the same message is processed by multiple handlers)
    if history and history[-1].get("message_id") == message.message_id:
        return

    history.append(
        {
            "message_id": message.message_id,
            "text": message.text,
            "user_id": message.from_user.id if message.from_user else 0,
            "username": message.from_user.username or message.from_user.first_name
            if message.from_user
            else "Usuario",
            "date": message.date,
        }
    )

    # Keep only last 20 messages
    context.chat_data["history"] = history[-20:]


async def get_telegram_history(
    message: Message, context: CallbackContext, limit: int = 8
) -> list[ModelMessage]:
    """
    Extracts the conversation history from the API context (chat_data) and the recursive reply chain.
    """
    bot_id = context.bot.id
    history_items: list[dict] = []
    seen_message_ids = set()

    # 1. Fetch from recursive reply chain (follows the specific thread)
    current = message.reply_to_message
    reply_chain_count = 0
    while current and reply_chain_count < 3:
        content = current.text or current.caption or ""
        if content:
            role = (
                "assistant"
                if current.from_user and current.from_user.id == bot_id
                else "user"
            )

            history_items.append(
                {
                    "role": role,
                    "content": content,
                    "date": current.date,
                    "message_id": current.message_id,
                }
            )
            seen_message_ids.add(current.message_id)
            reply_chain_count += 1
        current = current.reply_to_message

    # 2. Extract from general conversational context provided by the API (chat_data)
    chat_history = (
        context.chat_data.get("history", []) if context.chat_data is not None else []
    )
    # Only take the last 'limit' messages from chat_history
    for msg in chat_history[-(limit * 2) :]:
        # Avoid including the current message or already included messages from the reply chain
        if (
            msg["message_id"] == message.message_id
            or msg["message_id"] in seen_message_ids
        ):
            continue

        role = "assistant" if msg["user_id"] == bot_id else "user"
        history_items.append(
            {
                "role": role,
                "content": msg["text"],
                "date": msg["date"],
                "message_id": msg["message_id"],
            }
        )
        seen_message_ids.add(msg["message_id"])

    # 3. Sort chronologically and take only the last 'limit'
    history_items.sort(key=lambda x: x["date"])
    history_items = history_items[-limit:]

    # 4. Convert to ModelMessage
    final_history: list[ModelMessage] = []
    for item in history_items:
        if item["role"] == "assistant":
            final_history.append(
                ModelResponse(parts=[TextPart(content=item["content"])])
            )
        else:
            final_history.append(
                ModelRequest(parts=[UserPromptPart(content=item["content"])])
            )

    return final_history
