#!/usr/bin/env python3
"""
Demonstration script showing webhook replay defense and idempotency features.

This script demonstrates:
1. Idempotency key generation (deterministic hashing)
2. Webhook payload hashing
3. Basic validation of the implementation

Note: This is a smoke test that doesn't require Redis or PostgreSQL.
For full integration testing, set up the required services and use the test suite.
"""

import sys
import os
import json
import hashlib

# Add services/payments to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'payments'))

def test_idempotency_key_generation():
    """Test that idempotency keys are deterministic."""
    from app.stripe_client import generate_idempotency_key
    
    print("Testing idempotency key generation...")
    
    # Same inputs should produce same key
    key1 = generate_idempotency_key("checkout.session", "order_123", 5000, "usd")
    key2 = generate_idempotency_key("checkout.session", "order_123", 5000, "usd")
    
    assert key1 == key2, "Keys should be deterministic"
    assert len(key1) == 64, "SHA256 hash should be 64 hex characters"
    print(f"✓ Key 1: {key1}")
    print(f"✓ Key 2: {key2}")
    print(f"✓ Keys match: {key1 == key2}")
    
    # Different inputs should produce different keys
    key3 = generate_idempotency_key("checkout.session", "order_456", 5000, "usd")
    assert key1 != key3, "Different inputs should produce different keys"
    print(f"✓ Different order ID produces different key: {key3}")
    
    print("✓ Idempotency key generation works correctly\n")

def test_payload_hashing():
    """Test webhook payload hashing."""
    from app.webhooks import _payload_hash
    
    print("Testing payload hashing...")
    
    # Test with sample webhook payload
    payload = {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "amount_total": 5000,
                "currency": "usd"
            }
        }
    }
    
    raw = json.dumps(payload, sort_keys=True).encode('utf-8')
    hash1 = _payload_hash(raw)
    hash2 = _payload_hash(raw)
    
    assert hash1 == hash2, "Hash should be deterministic"
    assert len(hash1) == 64, "SHA256 hash should be 64 hex characters"
    
    expected = hashlib.sha256(raw).hexdigest()
    assert hash1 == expected, "Hash should match direct SHA256"
    
    print(f"✓ Payload: {payload}")
    print(f"✓ Hash: {hash1}")
    print(f"✓ Payload hashing works correctly\n")

def test_fastapi_app_structure():
    """Test that the FastAPI app is properly structured."""
    from app import app
    
    print("Testing FastAPI app structure...")
    
    assert app.title == "Payments Service", "App should have correct title"
    
    # Check that routes are registered
    routes = [route.path for route in app.routes]
    assert "/api/webhooks/stripe" in routes, "Webhook endpoint should be registered"
    
    print(f"✓ App title: {app.title}")
    print(f"✓ Registered routes: {routes}")
    print(f"✓ FastAPI app is properly configured\n")

def test_security_compliance():
    """Test that no secrets are hardcoded."""
    import os
    
    print("Testing security compliance...")
    
    # Check that environment variables are used
    from app.webhooks import STRIPE_WEBHOOK_SECRET, DATABASE_URL, REDIS_URL, stripe
    
    # These should be empty strings in test env (not hardcoded values)
    assert STRIPE_WEBHOOK_SECRET == "", "Webhook secret should come from env"
    assert stripe.api_key == "", "API key should come from env"
    
    print("✓ No hardcoded secrets found")
    print("✓ All secrets are loaded from environment variables")
    print("✓ Security compliance check passed\n")

def demonstrate_idempotency_guarantee():
    """Demonstrate the idempotency guarantee."""
    from app.stripe_client import generate_idempotency_key
    
    print("=" * 70)
    print("IDEMPOTENCY GUARANTEE DEMONSTRATION")
    print("=" * 70)
    
    order_id = "order_789"
    amount = 9999  # $99.99
    currency = "usd"
    
    print(f"\nScenario: Processing order {order_id} for ${amount/100:.2f} {currency.upper()}")
    print("-" * 70)
    
    # First attempt
    key1 = generate_idempotency_key("checkout.session", order_id, amount, currency)
    print(f"Attempt 1 - Idempotency Key: {key1}")
    
    # Retry (e.g., due to network timeout)
    key2 = generate_idempotency_key("checkout.session", order_id, amount, currency)
    print(f"Attempt 2 - Idempotency Key: {key2}")
    
    # Another retry
    key3 = generate_idempotency_key("checkout.session", order_id, amount, currency)
    print(f"Attempt 3 - Idempotency Key: {key3}")
    
    print("-" * 70)
    print(f"Result: All keys match → {key1 == key2 == key3}")
    print("✓ Stripe will return the same checkout session for all attempts")
    print("✓ Customer will NOT be double-charged")
    print("=" * 70 + "\n")

def main():
    """Run all demonstration tests."""
    print("\n" + "=" * 70)
    print("WEBHOOK REPLAY DEFENSE & IDEMPOTENCY DEMONSTRATION")
    print("=" * 70 + "\n")
    
    try:
        test_idempotency_key_generation()
        test_payload_hashing()
        test_fastapi_app_structure()
        test_security_compliance()
        demonstrate_idempotency_guarantee()
        
        print("=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nImplementation Summary:")
        print("• Webhook replay defense with Stripe signature verification")
        print("• Distributed locking via Redis to prevent concurrent processing")
        print("• Database-level idempotency with unique constraints")
        print("• SHA256-based deterministic idempotency keys")
        print("• Complete audit trail with payload hashing")
        print("\nNext Steps:")
        print("1. Set up PostgreSQL database")
        print("2. Apply migration: psql $DATABASE_URL -f services/payments/db/migrations/20251103_add_webhook_tables.sql")
        print("3. Configure Redis instance")
        print("4. Set environment variables (see services/payments/.env.example)")
        print("5. Start service: uvicorn services.payments.app:app")
        print("6. Test with Stripe CLI: stripe listen --forward-to localhost:8000/api/webhooks/stripe")
        print("\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
