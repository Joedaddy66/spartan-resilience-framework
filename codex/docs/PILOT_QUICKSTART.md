# Codex Pilot Quickstart Guide

Welcome to the Codex scroll validation system. This guide will help you quickly integrate with the deployed service.

## Service Endpoint

```
https://codex-api.example.com/v1
```

*(Replace with your actual deployment URL)*

## Authentication

All API requests require authentication using your `CODEX_API_KEY`. Include it in the Authorization header:

```bash
Authorization: Bearer YOUR_CODEX_API_KEY
```

## Quick Start

### 1. Submit a Scroll for Validation

Send a POST request to `/scrolls` with your data payload:

```bash
curl -X POST https://codex-api.example.com/v1/scrolls \
  -H "Authorization: Bearer YOUR_CODEX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "your-system-id",
    "content": {
      "title": "Sample Document",
      "body": "Your content here"
    },
    "facts": ["verified", "compliant"]
  }'
```

**Response:**
```json
{
  "scroll_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted",
  "tier": "T0",
  "correlation_id": "corr-1234567890"
}
```

### 2. Check Validation Status

Query the status of your scroll using its ID:

```bash
curl -X GET https://codex-api.example.com/v1/scrolls/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_CODEX_API_KEY"
```

**Response:**
```json
{
  "scroll_id": "550e8400-e29b-41d4-a716-446655440000",
  "tier": "T1",
  "status": "validated",
  "route_to": "T2",
  "diagnostics": {
    "schema_ok": true,
    "facts_ok": true,
    "missing": []
  },
  "content_hash": "a3b2c1d4e5f6...",
  "timestamp": "2025-10-30T19:45:24.084Z"
}
```

### 3. Retrieve Audit Trail

Get the complete audit ledger for your scroll:

```bash
curl -X GET https://codex-api.example.com/v1/scrolls/550e8400-e29b-41d4-a716-446655440000/ledger \
  -H "Authorization: Bearer YOUR_CODEX_API_KEY"
```

**Response:**
```json
{
  "scroll_id": "550e8400-e29b-41d4-a716-446655440000",
  "ledger": [
    {
      "tier": "T0",
      "timestamp": "2025-10-30T19:45:24.084Z",
      "actor": "T0_SPARTAN_CORE",
      "action": "validated",
      "content_hash": "a3b2c1d4e5f6...",
      "signature": "placeholder"
    },
    {
      "tier": "T1",
      "timestamp": "2025-10-30T19:45:25.120Z",
      "actor": "T1_SENTINEL",
      "action": "policy_check_passed",
      "content_hash": "a3b2c1d4e5f6...",
      "signature": "placeholder"
    }
  ]
}
```

## Required Payload Schema

Your scroll submission must include:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Identifier for your source system |
| `content` | object | Yes | The actual data being validated |
| `facts` | array | Yes | List of fact assertions about the content |

### Example Valid Payload

```json
{
  "source": "compliance-system-v2",
  "content": {
    "document_id": "DOC-2025-001",
    "title": "Q4 Compliance Report",
    "body": "All systems operational...",
    "metadata": {
      "department": "Legal",
      "classification": "Internal"
    }
  },
  "facts": [
    "reviewed_by_legal",
    "contains_no_pii",
    "approved_for_archive"
  ]
}
```

## Validation Tiers

Your scroll progresses through three validation tiers:

1. **T0 (Spartans)**: Schema validation, content hashing, basic fact checking
2. **T1 (Sentinels)**: Policy enforcement, enrichment, regulatory compliance
3. **T2 (Council)**: Final review, approval, archival

Each tier appends to the immutable audit ledger with cryptographic content hashes.

## Error Responses

### 400 Bad Request - Invalid Schema
```json
{
  "error": "validation_failed",
  "tier": "T0",
  "diagnostics": {
    "schema_ok": false,
    "missing": ["content", "facts"]
  }
}
```

### 401 Unauthorized - Invalid API Key
```json
{
  "error": "unauthorized",
  "message": "Invalid or missing API key"
}
```

### 429 Too Many Requests - Rate Limited
```json
{
  "error": "rate_limit_exceeded",
  "retry_after": 60
}
```

## Rate Limits

- **100 requests per minute** per API key
- **10,000 scrolls per day** per organization
- Contact support for enterprise limits

## Support

- **Documentation**: https://docs.codex-api.example.com
- **API Reference**: https://api-docs.codex-api.example.com
- **Support Email**: support@codex-api.example.com
- **Status Page**: https://status.codex-api.example.com

## Next Steps

1. **Test in Sandbox**: Use `sandbox.codex-api.example.com` for testing
2. **Review Documentation**: See full API reference at docs site
3. **Monitor Usage**: View API key usage in your dashboard
4. **Enable Webhooks**: Get real-time notifications of validation status changes

---

**Note**: This is a pilot deployment. Content hashes are SHA-256. Cryptographic signatures will be enabled in production (ed25519).
