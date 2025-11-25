BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'webhook_status') THEN
    CREATE TYPE webhook_status AS ENUM ('processing', 'processed', 'failed');
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS webhook_events (
  event_id      TEXT PRIMARY KEY,
  event_type    TEXT NOT NULL,
  payload_hash  TEXT NOT NULL,
  status        webhook_status NOT NULL DEFAULT 'processing',
  received_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS payments (
  session_id       TEXT PRIMARY KEY,
  customer_email   TEXT,
  amount           BIGINT,
  currency         TEXT,
  status           TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payment_intents (
  pi_id        TEXT PRIMARY KEY,
  amount       BIGINT,
  currency     TEXT,
  status       TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
  key          TEXT PRIMARY KEY,
  purpose      TEXT NOT NULL,
  scope        TEXT,          -- e.g., order_id
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  expires_at   TIMESTAMPTZ
);

COMMIT;
