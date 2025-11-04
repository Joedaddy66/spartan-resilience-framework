# Payments Service - Webhook Replay Defense & Idempotency

This service implements webhook replay defense and perfect idempotency for Stripe payment webhooks, ensuring exactly-once processing of payment events.

## Features

### 1. Webhook Replay Defense
- **Stripe Signature Verification**: Validates webhook signatures with 5-minute tolerance window
- **Event Deduplication**: Tracks processed events to prevent duplicate side-effects
- **Atomic Side-Effects**: Database constraints ensure idempotent writes
- **Distributed Locking**: Redis-based locks prevent concurrent processing

### 2. Perfect Idempotency
- **Idempotent Keys**: SHA256-based deterministic keys for Stripe API calls
- **Database Constraints**: `ON CONFLICT DO NOTHING` for all business writes
- **Audit Trail**: Complete event log with payload hashes for forensics

## Architecture

```
┌─────────────┐
│   Stripe    │
│  Webhook    │
└──────┬──────┘
       │ POST /api/webhooks/stripe
       ▼
┌─────────────────────────────┐
│  Signature Verification     │
│  (STRIPE_WEBHOOK_SECRET)    │
└──────┬──────────────────────┘
       │ Valid event
       ▼
┌─────────────────────────────┐
│  Distributed Lock (Redis)   │
│  lock:stripe:{event_id}     │
└──────┬──────────────────────┘
       │ Lock acquired
       ▼
┌─────────────────────────────┐
│  Database Idempotency       │
│  - Check if processed       │
│  - Mark processing          │
│  - Execute side-effects     │
│  - Mark processed           │
└─────────────────────────────┘
```

## Database Schema

### `webhook_events`
Event log with deduplication tracking:
- `event_id` (PK): Stripe event ID
- `event_type`: Event type (e.g., "checkout.session.completed")
- `payload_hash`: SHA256 of raw webhook body
- `status`: ENUM('processing', 'processed', 'failed')
- `received_at`, `processed_at`: Timestamps

### `payments`
Checkout session records:
- `session_id` (PK): Stripe checkout session ID
- `customer_email`, `amount`, `currency`, `status`
- Idempotent via `ON CONFLICT (session_id) DO NOTHING`

### `payment_intents`
Payment intent records:
- `pi_id` (PK): Stripe payment intent ID
- `amount`, `currency`, `status`
- Idempotent via `ON CONFLICT (pi_id) DO NOTHING`

### `idempotency_keys`
Catalog of idempotency keys used (optional):
- `key` (PK): SHA256 hash
- `purpose`, `scope`: Metadata
- `created_at`, `last_used_at`, `expires_at`

## Setup

### 1. Install Dependencies

```bash
pip install fastapi uvicorn stripe psycopg2-binary redis
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set:

```bash
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=postgresql://user:pass@localhost:5432/payments
REDIS_URL=redis://localhost:6379/0
```

### 3. Apply Database Migration

```bash
psql "$DATABASE_URL" -f services/payments/db/migrations/20251103_add_webhook_tables.sql
```

### 4. Start the Service

```bash
cd services/payments
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Testing

### Unit Tests

```bash
pytest services/payments/tests/test_webhook_replay_idempotency.py -v
```

### Local Stripe CLI Testing

```bash
# Terminal 1: Start service
uvicorn app:app --reload

# Terminal 2: Forward webhooks
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Terminal 3: Trigger test events
stripe trigger checkout.session.completed
stripe trigger payment_intent.succeeded
```

### Manual Replay Test

```bash
# Send duplicate webhook (should be idempotent)
curl -X POST http://localhost:8000/api/webhooks/stripe \
  -H "stripe-signature: test" \
  -d '{"id":"evt_test_123","type":"checkout.session.completed","data":{"object":{"id":"cs_123","amount_total":1000,"currency":"usd"}}}'
```

## Usage

### Creating Idempotent Checkout Sessions

```python
from services.payments.app.stripe_client import create_checkout_session

session = create_checkout_session(
    order_id="order_123",
    amount_cents=5000,  # $50.00
    currency="usd",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel"
)

# Calling again with same parameters returns same session
# (Stripe guarantees this via idempotency_key)
session2 = create_checkout_session(
    order_id="order_123",
    amount_cents=5000,
    currency="usd",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel"
)

assert session.id == session2.id
```

## Security Properties

### Three-Layer Shield

1. **Stripe Signature Verification**: Cryptographic proof of authenticity
2. **Redis Distributed Lock**: Prevents concurrent race conditions
3. **Database Constraints**: Final defense against duplicate writes

### Attack Scenarios

| Attack | Defense |
|--------|---------|
| Replay attack (duplicate webhook) | Event ID tracking + status check |
| Concurrent delivery | Redis NX lock (TTL 30s) |
| Tampered payload | Stripe signature verification fails → 400 |
| Old webhook replay | Signature tolerance window (5 min) |
| Double-charge | Idempotent database writes (ON CONFLICT) |

## Monitoring

### Key Metrics

- **Duplicate deliveries**: Count of 200 responses where event was already processed
- **Lock contention**: Failed lock acquisitions (rare, indicates high concurrency)
- **Processing latency**: Time from webhook receipt to completion
- **Failed signatures**: 400 responses (should be 0 in production)

### Signals

- ✅ 200 OK: Successfully processed (may be duplicate, check logs)
- ⚠️ 400 Bad Request: Invalid signature (Stripe will retry)
- 🔴 500 Error: System failure (lock, DB, or Redis down)

## Operational Runbook

See [docs/RUNBOOK_Payments_Webhooks.md](../../docs/RUNBOOK_Payments_Webhooks.md) for:
- Reproducing locally
- Unlocking stuck locks
- Deduplication semantics
- Troubleshooting

## Future Enhancements

- [ ] Idempotency budget cleanup (TTL-based key expiration)
- [ ] Dual-secret rotation window (graceful secret rotation)
- [ ] Chaos drills (automated duplicate-POST bursts)
- [ ] Webhook retry backoff tracking
- [ ] Event replay for disaster recovery

## References

- [Stripe Webhook Best Practices](https://stripe.com/docs/webhooks/best-practices)
- [Idempotency in Distributed Systems](https://stripe.com/blog/idempotency)
- [Exactly-Once Delivery](https://blog.pragmaticengineer.com/exactly-once-delivery/)
