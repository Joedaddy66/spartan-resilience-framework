<p align="center">
  <a href="https://pypi.org/project/qpprime/"><img alt="PyPI" src="https://img.shields.io/pypi/v/qpprime.svg"></a>
  <a href="https://pypi.org/project/qpprime/"><img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/qpprime.svg"></a>
  <a href="https://github.com/Joedaddy66/spartan-resilience-framework/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Joedaddy66/spartan-resilience-framework/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://Joedaddy66.github.io/spartan-resilience-framework/"><img alt="Docs" src="https://img.shields.io/badge/docs-mkdocs--material-informational"></a>
  <a href="https://github.com/Joedaddy66/spartan-resilience-framework/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/Joedaddy66/spartan-resilience-framework.svg"></a>
</p>

# Spartan Resilience Framework

A dual-civilization governance model for AI-human coexistence with integrated FinOps, telemetry, and policy enforcement.

## Project Structure
- **apps/**: Application services
  - **control-plane/**: FinOps policy enforcement and telemetry API
- **packages/**: Shared packages
  - **policies/**: OPA Rego policies for FinOps and governance
  - **telemetry/**: Resource monitoring and unit economics tracking
- **infra/**: Infrastructure as Code (Docker Compose, database schemas)
- **docs/**: MkDocs site content
- **slides/**: Presentations (.pptx)
- **src/**: Source code / notebooks
- **.github/workflows/**: CI automation with policy checks

## Features

### FinOps Policy Enforcement
- Budget guardrails and cost caps
- Required cost allocation tags
- Carbon efficiency requirements
- Promotion gates with quality metrics
- Integration with Open Policy Agent (OPA)

### Telemetry & Unit Economics
- Real-time inference and training metrics
- Calibrated cost models (per-token pricing)
- Energy consumption and carbon footprint tracking
- DORA metrics support

### Security & Provenance
- HMAC-signed event logs for audit trails
- No hardcoded secrets (environment variable configuration)
- Automated security scanning in CI
- Fail-closed policy enforcement

### Cloud Governance - Codex Guardrails v0.9.1
- **Multi-cloud controls matrix** for Azure, AWS, and GCP
- **OIDC-only authentication** (no long-term credentials)
- **Drift-sentinel validators** with daily compliance checks
- **Evidence artifacts** in JSON, SARIF, Markdown, and CSV formats
- **Service Control Policies** (SCPs) and Organization Policies
- See [CONTROLS_MATRIX.md](CONTROLS_MATRIX.md) for complete documentation

## Quick Start

### Control Plane API

```bash
# Set up environment
cd infra
cp .env.example .env
# Edit .env with your secrets

# Generate HMAC secret
python -c 'import secrets; print(secrets.token_hex(32))'

# Start services (PostgreSQL, OPA, Control Plane)
docker compose up -d

# Check health
curl http://localhost:8080/health
```

### Policy Check Example

```bash
curl -X POST http://localhost:8080/v1/gates/policy-check \
  -H "Content-Type: application/json" \
  -d '{
    "unit_cost_usd": 0.3,
    "cost_tags": {
      "team": "ai-team",
      "environment": "production"
    },
    "deployment_region": "us-west-2"
  }'
```

### Log Metrics

```bash
curl -X POST http://localhost:8080/v1/metrics/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "input_tokens": 100,
    "output_tokens": 50,
    "duration_ms": 250
  }'
```

## Security

This project implements comprehensive security measures:

- **Automated vulnerability scanning** with Safety and pip-audit
- **Static code analysis** with Bandit
- **Dependency monitoring** via Dependabot
- **Weekly security audits** via GitHub Actions
- **SBOM generation** for supply chain security

See [SECURITY.md](SECURITY.md) for details.

## Development

### Installation

```bash
# Install core package
pip install -e .

# Install control plane dependencies
pip install flask requests
```

### QPPrime Usage

```bash
# Command line interface for Q_p analysis
qpprime analyze --p 2 3 5 7
qpprime factor --p 13 17 19
qpprime table --p 2 3 5 --markdown
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_telemetry.py -v
python -m pytest tests/test_control_plane.py -v
```

### Copilot Coding Agent

This repository includes onboarding documentation for an automated Copilot coding agent and contributors in `.github/COPILOT_CODING_AGENT.md` and a minimal config at `.github/copilot-coding-agent.yml`.
Please follow the testing and review guidance there when opening changes.


### Policy Development

```bash
# Validate Rego policies
opa check packages/policies/finops.rego

# Test policy with input
echo '{"unit_cost_usd": 0.3, "cost_tags": {"team": "ai", "environment": "dev"}}' > input.json
opa eval --data packages/policies/finops.rego --input input.json 'data.finops'
```

## Configuration

All secrets and calibration values are configured via environment variables. See:
- `infra/.env.example` - Infrastructure configuration
- `apps/control-plane/README.md` - Control plane configuration
- `infra/README.md` - Infrastructure documentation

### Required Secrets
- `SAVE_HMAC_SECRET` - HMAC secret for event signing (required)
- `POSTGRES_PASSWORD` - Database password

### Cost Calibration
- `COST_PER_1K_INPUT_TOKENS` - Cost per 1000 input tokens (USD)
- `COST_PER_1K_OUTPUT_TOKENS` - Cost per 1000 output tokens (USD)
- `CARBON_INTENSITY_G_PER_KWH` - Grid carbon intensity (g CO2/kWh)
- `COMPUTE_COST_PER_HOUR` - GPU/compute cost per hour (USD)

### LeonideX RSA Audit
- `LEONIDEX_ENDPOINT` - LeonideX audit service endpoint URL
- `LEONIDEX_TOKEN` - LeonideX authentication token (Bearer token)

## RSA Audit Workflow

The repository includes automated RSA key auditing via the **LeonideX RSA Audit** workflow.

### Setting Up Repository Secrets

To use the audit workflow, configure the following repository secrets in GitHub:

1. Go to your repository Settings → Secrets and variables → Actions → New repository secret
2. Add these secrets:
   - **`LEONIDEX_ENDPOINT`**: The URL of your LeonideX audit service (e.g., `https://audit.example.com`)
   - **`LEONIDEX_TOKEN`**: Your authentication token for the LeonideX service

### Running the Workflow

#### Automatic Triggers
The workflow runs automatically on:
- Push to `main` branch
- Pull requests to `main` branch

#### Manual Execution
You can also trigger the workflow manually with a custom public key path:

1. Go to Actions → LeonideX RSA Audit → Run workflow
2. Optionally specify `pubkey_path` (default: `keys/sample.pub`)
3. Click "Run workflow"

Example with custom key:
```
pubkey_path: keys/my-custom-key.pub
```

### Workflow Artifacts

After each run, the workflow produces artifacts:
- **`report.json`**: JSON audit report with decision (PASS/FAIL) and depth information
- **`report.pdf`**: PDF report (if generated by the service)

Artifacts are retained for 30 days and can be downloaded from the workflow run page.

### Audit Output

The audit displays only sanitized, public-safe information:
- **Decision**: PASS or FAIL
- **Depth Information**: "Depth ≥ threshold" (no raw metrics)
- **Report Hash**: For verification purposes
- **Fingerprint**: Request identification

No formulas, dataset rows, or internal metrics are exposed.

## Documentation

- [Control Plane API](apps/control-plane/README.md)
- [Infrastructure Setup](infra/README.md)
- [Online Documentation](https://Joedaddy66.github.io/spartan-resilience-framework/)

## License
See [LICENSE](LICENSE).
