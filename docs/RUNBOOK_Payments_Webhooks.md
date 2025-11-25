# Payments Webhooks – Replay & Idempotency

**Signals**
- Stripe signature invalid → 400 in logs; Stripe will retry within 5 minutes.
- Duplicate delivery → 200 OK with no state change (lock + DB idempotency).

**To Reproduce Locally**
1. `stripe listen --forward-to localhost:8000/api/webhooks/stripe`
2. `stripe trigger checkout.session.completed`

**Unlock a stuck lock**
- Redis key: `lock:stripe:<event_id>` (TTL 30s). Normally auto-expires.

**Dedup Semantics**
- We log `webhook_events(event_id, status)`. If an event is `processed`, subsequent delivery is a no-op.

**Idempotent Business Writes**
- Inserts keyed by `session_id` or `pi_id` use `ON CONFLICT DO NOTHING`.
