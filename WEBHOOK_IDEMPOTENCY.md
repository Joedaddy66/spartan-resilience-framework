# Webhook Replay Defense & Idempotency - Quick Reference

This implementation provides production-ready webhook replay defense and idempotency for Stripe payments.

## 🔐 Security Features

✅ **Stripe Signature Verification** - Cryptographic proof of webhook authenticity  
✅ **No Hardcoded Secrets** - All credentials from environment variables  
✅ **Redis Distributed Locking** - Prevents concurrent race conditions  
✅ **Database Constraints** - Final defense against duplicate writes  
✅ **Payload Hashing** - SHA256 audit trail for forensics  

## 📂 File Structure

```
services/payments/
├── app/
│   ├── __init__.py              # FastAPI app factory
│   ├── webhooks.py              # Webhook endpoint with replay defense
│   └── stripe_client.py         # Idempotent Stripe API wrapper
├── db/
│   └── migrations/
│       └── 20251103_add_webhook_tables.sql  # Database schema
├── tests/
│   └── test_webhook_replay_idempotency.py   # Test suite
├── .env.example                 # Environment template
└── README.md                    # Full documentation
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
cp services/payments/.env.example services/payments/.env
# Edit .env with your credentials
```

### 2. Database Migration
```bash
psql $DATABASE_URL -f services/payments/db/migrations/20251103_add_webhook_tables.sql
```

### 3. Install Dependencies
```bash
pip install fastapi uvicorn stripe psycopg2-binary redis
```

### 4. Start Service
```bash
cd services/payments
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 5. Test Locally
```bash
# Terminal 1: Forward webhooks
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Terminal 2: Trigger test event
stripe trigger checkout.session.completed
```

## 🧪 Running Tests

```bash
# Run demonstration
python demo_webhook_idempotency.py

# Run full test suite (requires Redis & PostgreSQL)
pytest services/payments/tests/test_webhook_replay_idempotency.py -v
```

## 🎯 Key Implementation Details

### Idempotency Key Generation
```python
from services.payments.app.stripe_client import create_checkout_session

session = create_checkout_session(
    order_id="order_123",
    amount_cents=5000,
    currency="usd",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel"
)
# Same parameters → same idempotency key → same session ID
```

### Webhook Replay Defense
```
Webhook Received → Signature Verification → Redis Lock Acquisition
→ Database Dedup Check → Execute Side-Effects → Mark Processed
```

## 📊 Database Schema

| Table | Purpose | Idempotency Key |
|-------|---------|-----------------|
| `webhook_events` | Event log & dedup | `event_id` (Stripe event ID) |
| `payments` | Checkout sessions | `session_id` |
| `payment_intents` | Payment intents | `pi_id` |
| `idempotency_keys` | Key catalog (optional) | `key` (SHA256 hash) |

## 🔍 Monitoring & Operations

### Health Check
```bash
curl http://localhost:8000/docs  # FastAPI auto-generated docs
```

### Unlock Stuck Redis Lock
```bash
redis-cli DEL "lock:stripe:evt_123"
```

### Query Event Status
```sql
SELECT event_id, status, received_at, processed_at 
FROM webhook_events 
WHERE event_id = 'evt_123';
```

## 📚 Documentation

- **Full Guide**: [services/payments/README.md](services/payments/README.md)
- **Operations**: [docs/RUNBOOK_Payments_Webhooks.md](docs/RUNBOOK_Payments_Webhooks.md)
- **Architecture**: See README.md for three-layer security shield diagram

## 🔐 Environment Variables

```bash
STRIPE_API_KEY=sk_test_...              # Stripe secret key
STRIPE_WEBHOOK_SECRET=whsec_...          # Webhook signing secret
DATABASE_URL=postgresql://...            # PostgreSQL connection
REDIS_URL=redis://localhost:6379/0      # Redis connection
```

## ⚡ What This Buys You

✅ **Replay-proof**: Duplicate Stripe deliveries can't double-charge  
✅ **Exactly-once**: Upstream idempotency keys + downstream unique writes  
✅ **Auditable**: Every event logged; every action traceable  
✅ **Composable**: Locks + DB constraints + Stripe guarantees form three-layer shield  

## 🔜 Future Enhancements

- [ ] Idempotency budget cleanup (TTL-based key expiration)
- [ ] Dual-secret rotation window (graceful secret rotation)
- [ ] Chaos drills (automated duplicate-POST bursts)
- [ ] Webhook retry backoff tracking
- [ ] Event replay for disaster recovery

---

**Note**: This implementation follows the Spartan Resilience Framework's security principles:
- No hardcoded secrets (environment variables only)
- Fail-closed policy enforcement
- HMAC-signed audit trails (compatible with existing framework)
- Minimal attack surface
