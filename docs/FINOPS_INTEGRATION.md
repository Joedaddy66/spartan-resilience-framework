# FinOps Integration Guide

This document explains how the FinOps-as-Code integration addresses the requirements in SPEC-001.

## Overview

The Spartan Resilience Framework now includes:

1. **Control Plane API** - Policy enforcement and telemetry collection
2. **OPA/Rego Policies** - FinOps rules as code
3. **Telemetry System** - Unit economics and carbon tracking
4. **Infrastructure** - Secure deployment with PostgreSQL and OPA
5. **CI/CD Integration** - Automated policy checks

## Addressing SPEC-001 Requirements

### 1. Adapter & FinOps-as-Code Integration

#### FinOps Policy Gate (`apps/control-plane/src/main.py`)

**Status**: ✅ Implemented

The `/v1/gates/policy-check` endpoint now:
- Integrates with OPA via REST API (`check_policy_opa`)
- Falls back to embedded policy engine (`check_policy_embedded`)
- Evaluates all FinOps rules from `packages/policies/finops.rego`

**Configuration**:
```bash
# Enable OPA integration
export USE_OPA=true
export OPA_URL=http://localhost:8181
```

**Test**:
```bash
curl -X POST http://localhost:8080/v1/gates/policy-check \
  -H "Content-Type: application/json" \
  -d '{
    "unit_cost_usd": 0.3,
    "cost_tags": {"team": "ai", "environment": "dev"}
  }'
```

#### Policy Rules (`packages/policies/finops.rego`)

**Status**: ✅ Implemented

All SPEC-001 violation rules implemented:
- ✅ Budget caps (`unit_cost_usd > 0.5`)
- ✅ Total spend limits
- ✅ Required cost tags (team, environment)
- ✅ Promotion blocking (test pass rate, security scan)
- ✅ Carbon shift (intensity limits, region requirements)

**Test**:
```bash
opa check packages/policies/finops.rego
opa eval --data packages/policies/finops.rego --input test.json 'data.finops'
```

#### Database Connection (`infra/compose.yaml`)

**Status**: ✅ Secured

- Credentials loaded from environment variables
- `.env.example` provided as template
- `.env` excluded from Git via `.gitignore`
- Docker secrets supported for production

**Setup**:
```bash
cd infra
cp .env.example .env
# Edit .env with strong passwords
docker compose up -d
```

#### SAVE Protocol Secret (`apps/control-plane/src/main.py`)

**Status**: ✅ Secured

- `SAVE_HMAC_SECRET` must be set via environment variable
- Application fails to start if not set
- Strong secret generation documented

**Generate Secret**:
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

### 2. Telemetry & DORA/Unit Econ Metrics

#### Cost Model (`packages/telemetry/resource_monitor.py`)

**Status**: ✅ Calibrated

The cost model is now configurable via environment variables:
- `COST_PER_1K_INPUT_TOKENS` - Default: $0.001 (GPT-3.5-turbo rate)
- `COST_PER_1K_OUTPUT_TOKENS` - Default: $0.002
- `COMPUTE_COST_PER_HOUR` - Default: $1.00

**Calibration Example**:
```bash
# For GPT-4 Turbo pricing
export COST_PER_1K_INPUT_TOKENS=0.01
export COST_PER_1K_OUTPUT_TOKENS=0.03

# For custom GPU instance
export COMPUTE_COST_PER_HOUR=3.50
```

**Test**:
```python
from packages.telemetry.resource_monitor import ResourceMonitor
rm = ResourceMonitor()
metrics = rm.log_inference("gpt-4", 1000, 500, 1000)
print(f"Unit cost: ${metrics['unit_cost_usd']}")
```

#### Energy & Carbon (`packages/telemetry/resource_monitor.py`)

**Status**: ✅ Configurable

Real metrics integration via:
- `ENERGY_WH_PER_1K_TOKENS` - Energy per 1000 tokens
- `CARBON_INTENSITY_G_PER_KWH` - Grid carbon intensity

**Integration Points**:
1. Cloud provider APIs (AWS CloudWatch, Azure Monitor, GCP Monitoring)
2. Power monitoring APIs (e.g., RAPL, NVIDIA SMI)
3. Carbon intensity APIs (e.g., Electricity Maps, WattTime)

**Example Integration**:
```python
# In production, fetch from monitoring API
import requests
carbon_api = "https://api.carbonintensity.org.uk/regional"
response = requests.get(carbon_api)
intensity = response.json()['data'][0]['intensity']['forecast']

os.environ['CARBON_INTENSITY_G_PER_KWH'] = str(intensity)
```

#### Live Metrics Ingestion (`apps/control-plane/src/main.py`)

**Status**: ✅ Implemented

Endpoints for real-time metrics:
- `/v1/metrics/inference` - Log inference metrics
- `/v1/metrics/training` - Log training job metrics
- `/v1/metrics` - Retrieve all metrics

**Integration**:
```python
# In your model serving code
import requests

response = requests.post(
    "http://control-plane:8080/v1/metrics/inference",
    json={
        "model": "gpt-3.5-turbo",
        "input_tokens": 100,
        "output_tokens": 50,
        "duration_ms": 250,
        "metadata": {"user_id": "123", "session": "abc"}
    }
)
```

**Database Storage**:
Metrics are stored in PostgreSQL `biz_kpis` table (see `infra/init.sql`).

### 3. Rollout & CI/CD Orchestration

#### Rego Policies (`packages/policies/finops.rego`)

**Status**: ✅ Expanded

All rules from SPEC-001 Appendix implemented:
- Budget guardrails
- Cost tag requirements
- Carbon efficiency rules
- Promotion gates

**Add New Rules**:
```rego
# Add to finops.rego
deny contains msg if {
    input.new_requirement > threshold
    msg := "New requirement violated"
}
```

#### CI Policy Check (`.github/workflows/ci.yml`)

**Status**: ✅ Integrated

CI now includes:
1. **Policy Check Job**:
   - OPA setup
   - Rego syntax validation
   - Policy testing with conftest
2. **Build Job**:
   - Python tests
   - Telemetry module tests
   - Hardcoded secret detection
3. **Docker Build Job**:
   - Control plane image build
   - Docker Compose validation

**Local Testing**:
```bash
# Test CI steps locally
pytest tests/ -v
opa check packages/policies/finops.rego
docker build -f apps/control-plane/Dockerfile .
```

#### Build & Test Logic (`.github/workflows/ci.yml`)

**Status**: ✅ Implemented

CI workflow includes:
- Dependency installation for all workspaces
- Test execution for control-plane and telemetry
- Security scanning
- Docker image builds

**Future Enhancements** (not in scope for minimal changes):
- Predictive Test Selection (PTS)
- Workspace-specific build optimization
- Parallel test execution

#### Rollout Orchestration

**Status**: ⚠️ Requires Infrastructure

For production rollout, consider:

1. **GitOps with ArgoCD/Flux**:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: spartan-control-plane
spec:
  source:
    path: infra/k8s
    targetRevision: main
```

2. **Progressive Delivery with Flagger**:
```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: control-plane
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: control-plane
  analysis:
    threshold: 5
    maxWeight: 50
    stepWeight: 10
```

3. **Policy-Gated Deployments**:
```bash
# Pre-deployment policy check
curl -f http://control-plane/v1/gates/policy-check \
  -d @deployment-manifest.json || exit 1
kubectl apply -f deployment.yaml
```

## Testing

### Unit Tests
```bash
# All tests
pytest tests/ -v

# Specific modules
pytest tests/test_telemetry.py -v
pytest tests/test_control_plane.py -v
```

### Integration Tests
```bash
# Start services
cd infra
docker compose up -d

# Test policy enforcement
curl -X POST http://localhost:8080/v1/gates/policy-check \
  -d '{"unit_cost_usd": 0.6}'  # Should deny

# Test metrics logging
curl -X POST http://localhost:8080/v1/metrics/inference \
  -d '{"model": "test", "input_tokens": 100, "output_tokens": 50, "duration_ms": 250}'

# Verify in database
docker compose exec postgres psql -U postgres -d spartan_db \
  -c "SELECT * FROM biz_kpis;"
```

### Policy Tests
```bash
# Syntax check
opa check packages/policies/finops.rego

# Test with valid input
echo '{"unit_cost_usd": 0.3, "cost_tags": {"team": "ai", "environment": "dev"}}' \
  > valid.json
opa eval --data packages/policies/finops.rego --input valid.json 'data.finops.allow'
# Should output: true

# Test with invalid input
echo '{"unit_cost_usd": 0.6}' > invalid.json
opa eval --data packages/policies/finops.rego --input invalid.json 'data.finops.deny'
# Should output: ["Deployment missing...", "Unit cost..."]
```

## Production Deployment

### Security Checklist
- [ ] Set strong `SAVE_HMAC_SECRET`
- [ ] Use secure database passwords
- [ ] Enable TLS for all services
- [ ] Use Docker secrets (not environment variables)
- [ ] Set up network policies
- [ ] Enable audit logging
- [ ] Configure backup for PostgreSQL
- [ ] Set up monitoring and alerting

### Calibration Checklist
- [ ] Update `COST_PER_1K_INPUT_TOKENS` with actual rates
- [ ] Update `COST_PER_1K_OUTPUT_TOKENS` with actual rates
- [ ] Configure `CARBON_INTENSITY_G_PER_KWH` for region
- [ ] Set `COMPUTE_COST_PER_HOUR` for instance type
- [ ] Integrate with cloud provider metrics APIs
- [ ] Set up carbon intensity API integration

### Monitoring Checklist
- [ ] Set up metrics collection dashboards
- [ ] Configure alerting for policy violations
- [ ] Monitor DORA metrics
- [ ] Track unit economics trends
- [ ] Monitor carbon footprint
- [ ] Set up SLO/SLA tracking

## Troubleshooting

### Policy Check Fails
```bash
# Check OPA is running
curl http://localhost:8181/health

# Check policy is loaded
curl http://localhost:8181/v1/policies

# Test policy directly
curl -X POST http://localhost:8181/v1/data/finops \
  -d '{"input": {"unit_cost_usd": 0.3}}'
```

### Telemetry Not Recording
```bash
# Check control plane health
curl http://localhost:8080/health

# Check database connection
docker compose exec postgres psql -U postgres -d spartan_db -c "\dt"

# View logs
docker compose logs control-plane
```

### Docker Compose Issues
```bash
# Validate configuration
docker compose config

# Check service health
docker compose ps

# View logs
docker compose logs -f
```

## Next Steps

1. **Integrate with Cloud Provider APIs**:
   - AWS Cost Explorer for real-time costs
   - CloudWatch for metrics
   - Carbon intensity APIs

2. **Implement DORA Metrics Collection**:
   - Deployment frequency tracking
   - Lead time measurement
   - MTTR calculation
   - Change failure rate

3. **Add Advanced Policy Rules**:
   - Multi-region carbon optimization
   - Time-based pricing (off-peak discounts)
   - Reserved capacity utilization
   - Spot instance policies

4. **Enhance CI/CD**:
   - Predictive Test Selection (PTS)
   - Automated rollback on policy violations
   - Canary deployments with policy gates

5. **Production Hardening**:
   - Kubernetes deployment manifests
   - Service mesh integration
   - Observability stack (Prometheus, Grafana)
   - Disaster recovery procedures

## References

- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/latest/)
- [FinOps Foundation](https://www.finops.org/)
- [Green Software Foundation](https://greensoftware.foundation/)
- [DORA Metrics](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)
