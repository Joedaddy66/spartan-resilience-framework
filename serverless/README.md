# LeonideX Serverless Audit Service

This directory contains a Flask-based serverless endpoint stub for the LeonideX RSA audit service.

## Overview

The service provides sanitized, public-safe RSA key auditing functionality without exposing:
- Internal formulas or algorithms
- Raw dataset rows
- Internal metrics or scores

## Endpoints

### `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-02T17:52:23.184834+00:00",
  "service": "leonidex-audit-stub"
}
```

### `/audit` (POST)
Performs RSA key audit and returns a sanitized result.

**Request:**
```json
{
  "pubkey_path": "keys/sample.pub"
}
```

**Response:**
```json
{
  "schema": "leonidex-audit-v1",
  "decision": "PASS",
  "depth_floor_shown": "Depth ≥ threshold",
  "fingerprint": "73e4386914986020",
  "report_hash": "ae0b8321be728b080a0014cf2affadb2779d461aaf2f42d7c91841fabe95c63b",
  "signature": "simulated_signature_73e43869",
  "timestamp": "2025-11-02T17:52:23.215941+00:00",
  "pubkey_path": "keys/sample.pub"
}
```

## Running Locally

```bash
# Install dependencies
pip install flask

# Run the server
python serverless/cloud_run_main.py

# Test health endpoint
curl http://localhost:8080/health

# Test audit endpoint
curl -X POST http://localhost:8080/audit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"pubkey_path": "keys/sample.pub"}'
```

## Deployment

This stub is designed to be deployed to serverless platforms like:
- Google Cloud Run
- AWS Lambda (with appropriate adapter)
- Azure Functions (with appropriate adapter)

For Cloud Run deployment:
```bash
gcloud run deploy leonidex-audit \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Security

This is a **simulation stub** for testing purposes. In production:
- Implement proper authentication and authorization
- Use HTTPS/TLS for all communications
- Validate and sanitize all inputs
- Rate limit requests
- Monitor and log access patterns
