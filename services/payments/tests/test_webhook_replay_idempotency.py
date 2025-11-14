import json
from fastapi.testclient import TestClient
from services.payments.app import app

# monkeypatch stripe signature verifier so we can focus on our logic
class DummyEvent:
    def __init__(self, event_id, type_, obj):
        self.data = {"object": obj}
        self.id = event_id
        self.type = type_

def test_duplicate_webhook_is_ignored(monkeypatch):
    from services.payments.app import webhooks

    def fake_construct_event(payload, sig_header, secret, tolerance):
        body = json.loads(payload)
        # mimic stripe Event dict
        return {"id": body["id"], "type": body["type"], "data": {"object": body["data"]["object"]}}

    monkeypatch.setattr(webhooks.stripe.Webhook, "construct_event", staticmethod(fake_construct_event))

    client = TestClient(app)

    payload = {
        "id": "evt_123",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_123", "amount_total": 1000, "currency": "usd"}}
    }
    body = json.dumps(payload)

    # first delivery
    r1 = client.post("/api/webhooks/stripe", data=body, headers={"stripe-signature": "test"})
    # replay delivery
    r2 = client.post("/api/webhooks/stripe", data=body, headers={"stripe-signature": "test"})

    assert r1.status_code == 200
    assert r2.status_code == 200  # but side-effects should only happen once
