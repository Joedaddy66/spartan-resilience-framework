# Infrastructure

This directory contains both Docker Compose setup for local development and Terraform configuration for GCP IAM policy management.

## Docker Compose Setup

Docker Compose setup for the Spartan Resilience Framework.

### Services

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

---

## Terraform: GCP IAM Policy Management

The Terraform configuration in this directory manages GCP IAM organization policies for service account hardening with attestation and validation.

### Features

- **Policy Attestation**: Generates human-readable (Markdown) and machine-readable (JSON) attestations of applied policies
- **Post-Apply Validation**: Automatically validates that live GCP org policies match the expected configuration
- **Hardening Profiles**: Choose from `baseline`, `moderate`, or `strict` profiles
- **CI Integration**: Captures commit SHA and uploads attestations as artifacts

### Quick Start

1. **Set up GCP authentication:**
```bash
gcloud auth application-default login
```

2. **Configure variables:**
```bash
cd infra
terraform init

# Set required variables
export TF_VAR_project_id="your-gcp-project-id"
export TF_VAR_org_id="your-org-id"  # Optional
```

3. **Plan and apply:**
```bash
terraform plan
terraform apply
```

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `attestation_dir` | Directory for attestation artifacts | `artifacts` |
| `ci_commit_sha` | Git commit SHA (injected by CI) | `""` |
| `project_id` | GCP Project ID | `""` |
| `org_id` | GCP Organization ID | `""` |
| `policy_scope` | Scope: `project` or `org` | `project` |
| `use_managed_constraint` | Use managed constraints | `true` |
| `harden_profile` | Profile: `baseline`, `moderate`, or `strict` | `moderate` |

### Hardening Profiles

**Baseline**: Minimal hardening, most policies inherit from parent.

**Moderate** (default):
- Disable service account key creation and upload
- Disable API key creation
- Prevent privileged basic roles on default SAs
- Turn off automatic grants for default SAs

**Strict**: All moderate policies plus:
- Disable service account creation entirely

### Validation

The `validate_policies.sh` script compares expected policy modes against live GCP org policies:

```bash
./validate_policies.sh \
  --scope project \
  --project YOUR_PROJECT_ID \
  --modes-json artifacts/effective-modes.json \
  --use-managed true
```

Exit codes:
- `0`: Success, all policies match
- `42`: Validation failed, mismatches detected
- Other: Script error

### CI/CD Integration

See `.github/workflows/terraform.yml` for the main deployment workflow and `.github/workflows/terraform-pr-gate.yml` for PR validation.

**Workflows:**
- `terraform.yml`: Applies changes on push to main
- `terraform-pr-gate.yml`: Validates PRs, runs OPA policies to prevent downgrades
- `drift-sentinel.yml`: Weekly check for policy drift, opens GitHub issues on mismatch

**Artifacts uploaded:**
- `policy-attestation.md`: Human-readable attestation (retained 365 days)
- `effective-modes.json`: Machine-readable policy snapshot (retained 365 days)

### Repository Guardrails

This repo includes several safeguards:

1. **CODEOWNERS**: Platform team reviews required for infra changes
2. **OPA Policy**: Blocks PRs that weaken security constraints
3. **Drift Detection**: Weekly scheduled job detects manual policy changes
4. **Branch Protection**: Status checks must pass before merge

See `policy/opa/deny_downgrade.rego` for the OPA policy that prevents security downgrades.
