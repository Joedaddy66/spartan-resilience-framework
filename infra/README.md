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

---

## Cloud Governance - Controls Matrix v0.9.1

This infrastructure also supports the **Codex Guardrails Controls Matrix v0.9.1 (Rosetta)** for multi-cloud governance and policy enforcement.

### Components

#### Terraform Modules

- **`modules/github-oidc-aws/`**: AWS IAM role with GitHub OIDC federation (no long-term credentials)
- **`modules/gcp-org-policies/`**: GCP organization policies for service account key restrictions and storage security

#### Service Control Policies (SCPs)

- **`scp/deny-long-term-creds.json`**: Blocks IAM user access key creation (AWS)
- **`scp/deny-s3-public.json`**: Blocks S3 public access policies and ACLs
- **`scp/deny-cloudtrail-stop.json`**: Prevents CloudTrail logging disruption

#### Drift Sentinel Validators

- **`validators/aws-drift-sentinel.sh`**: Validates AWS guardrails (A1, A2, A6, A7, A8)
- **`validators/azure-drift-sentinel.sh`**: Validates Azure policies (A2, A3, A4, A5, A8)
- **`validators/gcp-drift-sentinel.sh`**: Validates GCP org policies (A1, A2, A8)

#### GitHub Actions Workflows

- **`.github/workflows/aws-drift-sentinel.yml`**: Daily AWS compliance checks
- **`.github/workflows/azure-drift-sentinel.yml`**: Daily Azure compliance checks
- **`.github/workflows/gcp-drift-sentinel.yml`**: Daily GCP compliance checks

### Quick Start - Cloud Guardrails

1. **Deploy OIDC infrastructure** (example for AWS):
   ```bash
   cd infra
   terraform init
   
   # Configure AWS OIDC role
   terraform apply -var="github_repo_subjects=['repo:YourOrg/YourRepo:*']"
   ```

2. **Configure GitHub repository secrets** (see [CONTROLS_MATRIX.md](../CONTROLS_MATRIX.md) for full list)

3. **Run validators manually**:
   ```bash
   # AWS (requires AWS credentials)
   AWS_ROLE_ARN=arn:aws:iam::123456789:role/github-actions \
     AWS_REGION=us-east-1 \
     AWS_ACCOUNT_ID=123456789 \
     bash validators/aws-drift-sentinel.sh
   
   # Azure (requires az login)
   bash validators/azure-drift-sentinel.sh
   
   # GCP (requires gcloud auth)
   GCP_PROJECT_ID=my-project \
     GCP_ORG_ID=organizations/123456 \
     bash validators/gcp-drift-sentinel.sh
   ```

4. **Review attestation artifacts** in `artifacts/` directory (JSON, SARIF, Markdown, CSV)

### Terraform Offline Validation (Egress Firewall-Safe)

When operating in environments with strict egress firewall rules, Terraform may fail due to:
- `checkpoint-api.hashicorp.com` - version checks
- `registry.terraform.io` - provider downloads  
- `metadata.google.internal` - GCE metadata probes (when unauthenticated)

Use the reusable composite action to validate Terraform offline:

```yaml
- uses: ./.github/actions/tf-offline-validate
  with:
    terraform_version: '1.9.5'
    working_directory: 'infra'
    gcp_workload_identity_provider: ${{ secrets.GCP_WIF_PROVIDER }}
    gcp_service_account: ${{ secrets.GCP_WIF_SA }}
    aws_role_arn: ${{ secrets.AWS_ROLE_ARN }}
    azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
    azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
    azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

**How it works:**
1. Pre-warms provider cache before firewall enforcement
2. Disables checkpoint calls via `CHECKPOINT_DISABLE=1`
3. Authenticates to clouds to prevent metadata probes
4. Validates using cached providers (no network required)

See `.github/actions/tf-offline-validate/README.md` for local CLI equivalents and detailed usage.

### Attestation Artifacts

Validators generate evidence files in multiple formats:

- **JSON**: Machine-readable attestation with control status
- **SARIF**: Security findings for GitHub Code Scanning
- **Markdown**: Human-readable reports
- **CSV**: Spreadsheet-compatible exports for non-compliant resources

### Documentation

See [CONTROLS_MATRIX.md](../CONTROLS_MATRIX.md) for:
- Complete control coverage matrix
- CLI verification examples
- Severity and ownership mappings
- Implementation guides
- Roadmap to v1.0.0
