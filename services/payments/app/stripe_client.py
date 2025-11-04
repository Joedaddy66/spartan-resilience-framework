import os, hashlib
import stripe

stripe.api_key = os.environ.get("STRIPE_API_KEY", "")

def _idem_key(purpose: str, *parts: str) -> str:
    raw = "|".join([purpose, *[str(p) for p in parts]])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def create_checkout_session(order_id: str, amount_cents: int, currency: str, success_url: str, cancel_url: str):
    key = _idem_key("checkout.session", order_id, amount_cents, currency)
    return stripe.checkout.Session.create(
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{
            "price_data": {
                "currency": currency,
                "product_data": {"name": f"Order {order_id}"},
                "unit_amount": amount_cents,
            },
            "quantity": 1
        }],
        client_reference_id=order_id,
        idempotency_key=key,  # <- the shield
    )
