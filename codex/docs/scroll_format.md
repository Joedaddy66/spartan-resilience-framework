# Scroll Format

A **Scroll** is the atomic unit of data flowing through the Codex tier system. Each scroll contains:

## Structure

```python
{
  "id": "unique-scroll-id",
  "header": {
    "tier": "T0|T1|T2|END",
    "kind": "INIT|VALIDATED|DISPATCH",
    "route_to": "T0|T1|T2|END",
    "created_at": 1234567890.123,
    "correlation_id": "corr-id"
  },
  "payload": {
    "raw": { ... },
    # arbitrary data
  },
  "provenance": {
    "source": "origin-system",
    "actor": "agent-name",
    "signatures": [],
    "content_hash": "sha256-hash"
  },
  "diagnostics": {
    "schema_ok": true,
    "missing": [],
    "facts_ok": true
  }
}
```

## Fields

- **id**: Unique identifier for the scroll
- **header**: Routing and metadata
  - **tier**: Current processing tier
  - **kind**: Type of scroll (INIT, VALIDATED, DISPATCH)
  - **route_to**: Next tier to route to
  - **created_at**: Timestamp
  - **correlation_id**: Correlation ID for tracking
- **payload**: Actual data being processed
- **provenance**: Origin and integrity information
  - **source**: Source system
  - **actor**: Agent that created/modified the scroll
  - **signatures**: Cryptographic signatures (placeholder)
  - **content_hash**: SHA-256 hash of payload for integrity
- **diagnostics**: Validation results and metadata

## Tier Flow

1. **T0 (Spartans)**: Initial validation of schema, content hash, and basic facts
2. **T1 (Sentinels)**: Policy checks and enrichment
3. **T2 (Council)**: Final review and approval
4. **END**: Terminal state

Each tier can promote to the next tier or bounce back to a previous tier for corrections.
