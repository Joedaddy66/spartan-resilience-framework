from __future__ import annotations
import os, json, hashlib
from typing import Any, Dict
from fastapi import APIRouter, Request, Response, HTTPException
import stripe
import psycopg2
import psycopg2.extras
import redis

router = APIRouter()

# --- Config ---
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/payments")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
LOCK_TTL_SEC = 30
SIG_TOLERANCE_SEC = 300  # 5 minutes

stripe.api_key = os.environ.get("STRIPE_API_KEY", "")

# --- Clients ---
_redis_client = None

def _get_redis():
    """Lazy initialization of Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client

def _pg():
    return psycopg2.connect(DATABASE_URL)

def _payload_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def _acquire_lock(event_id: str) -> bool:
    # NX+EX yields a one-shot lock; prevents concurrent double-processing
    return bool(_get_redis().set(f"lock:stripe:{event_id}", "1", nx=True, ex=LOCK_TTL_SEC))

def _release_lock(event_id: str) -> None:
    _get_redis().delete(f"lock:stripe:{event_id}")

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request) -> Response:
    raw = await request.body()

    sig_header = request.headers.get("stripe-signature")
    if not sig_header or not STRIPE_WEBHOOK_SECRET:
        # Still return 200 to avoid Stripe retries leaking info, but log internally
        return Response(status_code=200)

    try:
        event = stripe.Webhook.construct_event(
            payload=raw,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET,
            tolerance=SIG_TOLERANCE_SEC,
        )
    except Exception:
        # Signature invalid or too old; acknowledge with 400 so Stripe may retry within window
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_id: str = event.get("id", "")
    event_type: str = event.get("type", "")
    body_hash = _payload_hash(raw)

    # Cheap concurrent guard first
    if not _acquire_lock(event_id):
        # Duplicate (concurrent) delivery; acknowledge idempotently
        return Response(status_code=200)

    try:
        with _pg() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # If we already processed this event, exit cleanly
                cur.execute(
                    "SELECT status FROM webhook_events WHERE event_id = %s",
                    (event_id,),
                )
                row = cur.fetchone()
                if row and row["status"] == "processed":
                    return Response(status_code=200)

                # mark "processing" (or noop if exists)
                cur.execute(
                    """
                    INSERT INTO webhook_events(event_id, event_type, payload_hash, status, received_at)
                    VALUES (%s, %s, %s, 'processing', NOW())
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (event_id, event_type, body_hash),
                )

                # --- business side-effects (idempotent upserts) ---
                if event_type == "checkout.session.completed":
                    session = event["data"]["object"]
                    session_id = session["id"]
                    customer_email = session.get("customer_details", {}).get("email")
                    amount = session.get("amount_total")
                    currency = session.get("currency")

                    # idempotent write keyed by session_id
                    cur.execute(
                        """
                        INSERT INTO payments (session_id, customer_email, amount, currency, status, created_at)
                        VALUES (%s, %s, %s, %s, 'succeeded', NOW())
                        ON CONFLICT (session_id) DO NOTHING
                        """,
                        (session_id, customer_email, amount, currency),
                    )

                elif event_type == "payment_intent.succeeded":
                    pi = event["data"]["object"]
                    pi_id = pi["id"]
                    amount = pi.get("amount_received")
                    currency = pi.get("currency")

                    cur.execute(
                        """
                        INSERT INTO payment_intents (pi_id, amount, currency, status, created_at)
                        VALUES (%s, %s, %s, 'succeeded', NOW())
                        ON CONFLICT (pi_id) DO NOTHING
                        """,
                        (pi_id, amount, currency),
                    )
                # else: accept harmlessly, but do nothing

                # mark processed
                cur.execute(
                    "UPDATE webhook_events SET status='processed', processed_at=NOW() WHERE event_id=%s",
                    (event_id,),
                )

        return Response(status_code=200)
    finally:
        _release_lock(event_id)
