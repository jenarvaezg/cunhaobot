from typing import cast
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    MessageEntity,
)
from telegram.ext import CallbackContext

from tg.decorators import log_update
from models.gift import GiftType, GIFT_PRICES, GIFT_EMOJIS, GIFT_NAMES
from infrastructure.datastore.user import user_repository


@log_update
async def handle_gift_command(update: Update, context: CallbackContext) -> None:
    """Show the menu to select a gift."""
    message = update.effective_message
    if not message:
        return

    # Determine receiver
    receiver = None
    if message.reply_to_message:
        receiver = message.reply_to_message.from_user
    else:
        # Check for mentions
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
        )
        for entity, text in entities.items():
            if entity.type == MessageEntity.TEXT_MENTION:
                receiver = entity.user
                break
            elif entity.type == MessageEntity.MENTION:
                username = text.lstrip("@")
                # Look up user in DB
                receiver = await user_repository.get_by_username(username)
                if not receiver:
                    await message.reply_text(
                        f"⚠️ No conozco a @{username}. Dile que hable conmigo primero."
                    )
                    return
                break

    # Basic validation
    if (
        not receiver
        or not message.from_user
        or str(receiver.id) == str(message.from_user.id)
        or (hasattr(receiver, "is_bot") and receiver.is_bot)
    ):
        await message.reply_text(
            "⚠️ Para regalar algo, responde a un mensaje o menciona al afortunado (ej: /regalar @usuario)."
        )
        return

    keyboard = []
    row = []
    for gift_type in GiftType:
        price = GIFT_PRICES[gift_type]
        text = f"{GIFT_EMOJIS[gift_type]} {GIFT_NAMES[gift_type]} ({price} ⭐️)"
        # Format: gift_sel:receiver_id:gift_type
        data = f"gift_sel:{receiver.id}:{gift_type.value}"
        row.append(InlineKeyboardButton(text, callback_data=data))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        f"¿Qué detalle quieres tener con {receiver.first_name}?",
        reply_markup=reply_markup,
    )


@log_update
async def handle_gift_selection(update: Update, context: CallbackContext) -> None:
    """Handle the button press and send the invoice."""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data
    if not data or not data.startswith("gift_sel:"):
        return

    try:
        _, receiver_id_str, gift_type_str = data.split(":")
        receiver_id = int(receiver_id_str)
        gift_type = GiftType(gift_type_str)
    except ValueError:
        return

    price = GIFT_PRICES[gift_type]
    title = f"{GIFT_EMOJIS[gift_type]} Regalo: {GIFT_NAMES[gift_type]}"
    description = f"Un {GIFT_NAMES[gift_type]} digital para el chaval."

    if not query.message:
        return

    message = cast(Message, query.message)
    chat_id = message.chat_id

    # Payload: gift:chat_id:receiver_id:gift_type
    payload = f"gift:{chat_id}:{receiver_id}:{gift_type.value}"

    prices = [LabeledPrice(title, price)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token="",  # Empty for XTR
        currency="XTR",
        prices=prices,
        start_parameter="gift-giving",
    )

    # Clean up the selection menu
    try:
        await message.delete()
    except Exception:
        pass
