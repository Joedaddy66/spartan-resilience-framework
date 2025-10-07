# Control Plane

The Control Plane provides FinOps policy enforcement and telemetry tracking for the Spartan Resilience Framework.

## Features

- **FinOps Policy Enforcement**: Integrates with OPA to enforce budget caps, cost tags, carbon limits, and promotion gates
- **Telemetry & Metrics**: Tracks inference/training metrics with unit economics and carbon footprint
- **Event Provenance**: HMAC-signed append-only event log for audit trails
- **Real-time Monitoring**: REST API for metrics collection and policy checks

## API Endpoints

### Health Check
```
GET /health
```

### Policy Check
```
POST /v1/gates/policy-check
Content-Type: application/json

{
  "unit_cost_usd": 0.3,
  "cost_tags": {
    "team": "ai-team",
    "environment": "production"
  },
  "deployment_region": "us-west-2",
  "carbon_intensity_g_per_kwh": 250
}
```

### Log Inference Metrics
```
POST /v1/metrics/inference
Content-Type: application/json

{
  "model": "gpt-3.5-turbo",
  "input_tokens": 100,
  "output_tokens": 50,
  "duration_ms": 250
}
```

### Log Training Metrics
```
POST /v1/metrics/training
Content-Type: application/json

{
  "model": "custom-model-v1",
  "duration_hours": 2.5,
  "gpu_count": 4
}
```

### Get Metrics
```
GET /v1/metrics
```

## Configuration

Configure via environment variables (see `infra/.env.example`):

- `SAVE_HMAC_SECRET`: HMAC secret for event signing (required)
- `OPA_URL`: OPA endpoint URL (default: http://localhost:8181)
- `USE_OPA`: Use OPA or embedded policy engine (default: true)
- `COST_PER_1K_INPUT_TOKENS`: Cost per 1000 input tokens in USD
- `COST_PER_1K_OUTPUT_TOKENS`: Cost per 1000 output tokens in USD
- `CARBON_INTENSITY_G_PER_KWH`: Carbon intensity of grid in g CO2/kWh

## Running Locally

```bash
# Set required environment variables
export SAVE_HMAC_SECRET=$(python -c 'import secrets; print(secrets.token_hex(32))')

# Install dependencies
pip install flask requests

# Run the server
python apps/control-plane/src/main.py
```

## Security

- All events are HMAC-signed for provenance tracking
- Secrets must be provided via environment variables
- Fail-closed policy enforcement (denies if OPA unavailable)
- No hardcoded credentials
