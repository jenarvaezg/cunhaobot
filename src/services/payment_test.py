import pytest

from models.gift import GiftType
from services.payment import (
    GiftPayment,
    InvalidPaymentPayload,
    PosterPayment,
    SubscriptionPayment,
    parse_payment_payload,
)


class TestParsePaymentPayload:
    """Paid fulfillment payload parsing is centralized so Regalo, Póster and
    Suscripción Premium no longer depend on ad hoc string handling spread
    across the payment handler."""

    def test_gift_with_chat(self):
        result = parse_payment_payload("gift:-100:200:palillo")
        assert result == GiftPayment(
            chat_id=-100, receiver_id=200, gift_type=GiftType.PALILLO
        )

    def test_gift_legacy_without_chat(self):
        result = parse_payment_payload("gift:200:cognac")
        assert isinstance(result, GiftPayment)
        assert result.chat_id is None
        assert result.receiver_id == 200
        assert result.gift_type is GiftType.COGNAC

    def test_subscription(self):
        result = parse_payment_payload("subs_month_-1009999")
        assert result == SubscriptionPayment(target_chat_id=-1009999)

    def test_poster_request_id(self):
        # Anything else is treated as a Póster request id (or legacy phrase).
        result = parse_payment_payload("poster-abc-123")
        assert result == PosterPayment(payload="poster-abc-123")

    def test_empty_payload_is_invalid(self):
        with pytest.raises(InvalidPaymentPayload):
            parse_payment_payload("")

    def test_gift_invalid_type_is_invalid(self):
        with pytest.raises(InvalidPaymentPayload):
            parse_payment_payload("gift:-100:200:diamond")

    def test_gift_non_numeric_receiver_is_invalid(self):
        with pytest.raises(InvalidPaymentPayload):
            parse_payment_payload("gift:-100:abc:palillo")

    def test_subscription_non_numeric_is_invalid(self):
        with pytest.raises(InvalidPaymentPayload):
            parse_payment_payload("subs_month_notanumber")
