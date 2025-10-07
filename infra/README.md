# Infrastructure

Docker Compose setup for the Spartan Resilience Framework.

## Services

- **PostgreSQL**: Metrics and event storage
- **OPA**: Open Policy Agent for FinOps policy enforcement
- **Control Plane**: API server for policy checks and telemetry

## Quick Start

1. Copy the example environment file:
```bash
cd infra
cp .env.example .env
```

2. Edit `.env` and set secure values:
```bash
# Generate HMAC secret
python -c 'import secrets; print(secrets.token_hex(32))'

# Set strong database password
# Update cost calibration values for your cloud provider
```

3. Start services:
```bash
docker compose up -d
```

4. Check health:
```bash
curl http://localhost:8080/health
```

## Database Schema

The PostgreSQL database includes tables for:

- `event_log`: Append-only event log with HMAC signatures
- `biz_kpis`: Business metrics and unit economics
- `deployments`: Deployment tracking with policy results
- `dora_metrics`: DORA metrics (deployment frequency, lead time, MTTR, change failure rate)

Schema is initialized automatically from `init.sql`.

## OPA Policy Server

The OPA container loads policies from `packages/policies/finops.rego` and provides:

- Budget guardrails
- Cost tag requirements
- Promotion gates
- Carbon efficiency rules

Test policies:
```bash
curl -X POST http://localhost:8181/v1/data/finops \
  -H "Content-Type: application/json" \
  -d '{"input": {"unit_cost_usd": 0.3, "cost_tags": {"team": "ai", "environment": "dev"}}}'
```

## Security Best Practices

1. **Never commit `.env` to Git** - it contains secrets
2. Use strong, unique passwords for all services
3. Generate HMAC secret with cryptographically secure random generator
4. Rotate secrets regularly
5. Use Docker secrets in production (not environment variables)
6. Limit network exposure (use internal networks)

## Production Deployment

For production:

1. Use Docker Secrets or a secret manager (AWS Secrets Manager, HashiCorp Vault, etc.)
2. Set up TLS/SSL for all services
3. Configure proper backup for PostgreSQL
4. Enable audit logging
5. Set up monitoring and alerting
6. Use read replicas for high availability
7. Implement proper RBAC

## Calibration

Update environment variables in `.env` to match your cloud provider costs:

- `COST_PER_1K_INPUT_TOKENS`: Your actual cost per 1K input tokens
- `COST_PER_1K_OUTPUT_TOKENS`: Your actual cost per 1K output tokens
- `ENERGY_WH_PER_1K_TOKENS`: Measured energy per 1K tokens
- `CARBON_INTENSITY_G_PER_KWH`: Grid carbon intensity in your region
- `COMPUTE_COST_PER_HOUR`: GPU/compute instance cost per hour

Refer to your cloud provider documentation for accurate values.
