"""Centralized parsing of Telegram payment payloads.

Paid fulfillment covers three products — Regalo, Póster and Suscripción
Premium — that historically were distinguished by ad hoc ``startswith`` checks
and inline ``split`` parsing inside the payment handler. This module turns a
raw payload string into a typed payment intent so callers route on the parsed
result instead of reasoning about string prefixes.
"""

from dataclasses import dataclass

from models.gift import GiftType


@dataclass(frozen=True)
class GiftPayment:
    """A Regalo from one Perfil to another within a Chat."""

    receiver_id: int
    gift_type: GiftType
    chat_id: int | None = None


@dataclass(frozen=True)
class SubscriptionPayment:
    """A Suscripción Premium extension scoped to a Chat."""

    target_chat_id: int


@dataclass(frozen=True)
class PosterPayment:
    """A Póster request, identified by its stored request id (or legacy phrase)."""

    payload: str


ParsedPayment = GiftPayment | SubscriptionPayment | PosterPayment

_GIFT_PREFIX = "gift:"
_SUBSCRIPTION_PREFIX = "subs_month_"


class InvalidPaymentPayload(ValueError):
    """Raised when a payment payload cannot be parsed into a known intent."""


def parse_payment_payload(payload: str) -> ParsedPayment:
    """Parse a raw invoice payload into a typed payment intent.

    Raises ``InvalidPaymentPayload`` for empty or malformed Regalo/Suscripción
    payloads. Any unrecognized payload is treated as a Póster request id, which
    preserves the historical fallback where the payload could be a plain phrase.
    """
    if not payload:
        raise InvalidPaymentPayload("empty payload")

    if payload.startswith(_GIFT_PREFIX):
        return _parse_gift(payload)

    if payload.startswith(_SUBSCRIPTION_PREFIX):
        return _parse_subscription(payload)

    return PosterPayment(payload=payload)


def _parse_gift(payload: str) -> GiftPayment:
    parts = payload.split(":")
    # Modern: gift:chat_id:receiver_id:gift_type
    # Legacy: gift:receiver_id:gift_type (delivered in the originating chat)
    if len(parts) == 4:
        _, chat_id_str, receiver_id_str, gift_type_str = parts
        chat_id: int | None = _to_int(chat_id_str, payload)
    elif len(parts) == 3:
        _, receiver_id_str, gift_type_str = parts
        chat_id = None
    else:
        raise InvalidPaymentPayload(f"malformed gift payload: {payload!r}")

    receiver_id = _to_int(receiver_id_str, payload)
    try:
        gift_type = GiftType(gift_type_str)
    except ValueError as exc:
        raise InvalidPaymentPayload(
            f"unknown gift type {gift_type_str!r} in {payload!r}"
        ) from exc

    return GiftPayment(receiver_id=receiver_id, gift_type=gift_type, chat_id=chat_id)


def _parse_subscription(payload: str) -> SubscriptionPayment:
    target_chat_id = _to_int(payload.replace(_SUBSCRIPTION_PREFIX, "", 1), payload)
    return SubscriptionPayment(target_chat_id=target_chat_id)


def _to_int(value: str, payload: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise InvalidPaymentPayload(
            f"expected integer, got {value!r} in {payload!r}"
        ) from exc
