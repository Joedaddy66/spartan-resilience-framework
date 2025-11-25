import os, hashlib
import stripe

stripe.api_key = os.environ.get("STRIPE_API_KEY", "")

def generate_idempotency_key(purpose: str, *parts: str) -> str:
    """
    Generate a deterministic idempotency key from the given purpose and parts.
    
    Args:
        purpose: The purpose of the operation (e.g., "checkout.session")
        *parts: Variable parts that uniquely identify this operation
        
    Returns:
        A SHA256 hex digest that can be used as an idempotency key
    """
    raw = "|".join([purpose, *[str(p) for p in parts]])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def create_checkout_session(order_id: str, amount_cents: int, currency: str, success_url: str, cancel_url: str):
    key = generate_idempotency_key("checkout.session", order_id, amount_cents, currency)
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
