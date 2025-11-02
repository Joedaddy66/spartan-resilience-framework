# Copilot Instructions for Spartan Resilience Framework

## Project Overview

The Spartan Resilience Framework is a dual-civilization governance model for AI-human coexistence with integrated FinOps, telemetry, and policy enforcement. It combines:
- **QPPrime**: A quadratic polynomial prime analysis toolkit (Python package published to PyPI)
- **Control Plane**: FinOps policy enforcement and telemetry API (Flask-based service)
- **Cloud Governance**: Multi-cloud drift detection and compliance enforcement (Azure, AWS, GCP)

## Repository Structure

```
├── apps/
│   └── control-plane/        # Flask API for policy enforcement and telemetry
├── packages/
│   ├── policies/              # OPA Rego policies for FinOps governance
│   └── telemetry/            # Resource monitoring and unit economics tracking
├── src/qpprime/              # Main Python package (number theory toolkit)
├── tests/                    # Pytest test suite
├── infra/                    # Infrastructure as Code (Docker Compose, schemas)
├── docs/                     # MkDocs documentation site
├── .github/workflows/        # CI/CD pipelines
└── pyproject.toml            # Python package configuration
```

## Tech Stack

- **Language**: Python 3.9+ (primary: 3.11+)
- **Package Manager**: pip, setuptools
- **Web Framework**: Flask (for control-plane API)
- **Policy Engine**: Open Policy Agent (OPA) with Rego
- **Testing**: pytest
- **Documentation**: MkDocs with Material theme
- **CI/CD**: GitHub Actions
- **Container**: Docker, Docker Compose
- **Cloud**: Azure, AWS, GCP (multi-cloud governance)

## Development Workflow

### Installation

```bash
# Install core package in editable mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Install control-plane dependencies
pip install flask requests

# Install dev dependencies
pip install pytest mkdocs mkdocs-material
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_qp.py -v          # QPPrime tests
python -m pytest tests/test_control_plane.py -v  # Policy tests
python -m pytest tests/test_telemetry.py -v   # Telemetry tests
python -m pytest tests/test_security.py -v    # Security tests
```

### Building and Documentation

```bash
# Build documentation
mkdocs build

# Serve docs locally
mkdocs serve

# Build Docker image
docker build -f apps/control-plane/Dockerfile -t spartan-control-plane:test .

# Validate Docker Compose
cd infra && docker compose config
```

### Policy Development

```bash
# Validate Rego policies
opa check packages/policies/finops.rego

# Test policies with conftest
conftest test <input.json> -p packages/policies/finops.rego
```

## Coding Standards

### Python Style
- Follow PEP 8 conventions
- Use type hints where appropriate
- Prefer explicit over implicit
- Keep functions focused and modular
- Use meaningful variable and function names

### Security Requirements (CRITICAL)
1. **NO hardcoded secrets**: All secrets MUST be environment variables
   - Use `SAVE_HMAC_SECRET`, `POSTGRES_PASSWORD`, etc.
   - Never commit API keys, tokens, or credentials
2. **Input validation**: Validate all external inputs
3. **Dependency scanning**: Run `safety check` before adding new dependencies
4. **HMAC signing**: All event logs must be HMAC-signed for audit trails
5. **Fail-closed**: Policy enforcement must fail closed (deny by default)

### Configuration Management
- All configuration via environment variables
- Use `.env.example` files as templates (never commit `.env`)
- Cost calibration constants in environment:
  - `COST_PER_1K_INPUT_TOKENS`
  - `COST_PER_1K_OUTPUT_TOKENS`
  - `CARBON_INTENSITY_G_PER_KWH`
  - `COMPUTE_COST_PER_HOUR`

## Testing Requirements

### Test Coverage
- Write tests for all new features
- Maintain existing test structure:
  - `test_qp.py` - Number theory algorithms
  - `test_control_plane.py` - Policy enforcement
  - `test_telemetry.py` - Metrics and monitoring
  - `test_security.py` - Security checks
- Use pytest fixtures for common setup
- Test both success and failure paths

### Security Testing
All PRs must pass:
- `safety check` - Dependency vulnerability scan
- Secret detection (no "dev-secret" placeholders)
- Policy validation (OPA check)
- Static analysis (if added)

## CI/CD Pipelines

### Main CI Workflow (`.github/workflows/ci.yml`)
1. **Policy Check**: OPA Rego policy validation
2. **Build**: Python tests, dependency installation
3. **Security**: Safety check, secret detection
4. **Documentation**: MkDocs build
5. **Docker**: Container build validation

### Drift Sentinels
- Azure, AWS, GCP drift detection workflows
- Run daily to check cloud compliance
- Use OIDC authentication (no long-term credentials)

### Release Process
- Use Release Drafter for automated release notes
- Label PRs: `feature`, `bug`, `docs`, `security`
- PyPI publishing via GitHub Actions on tag
- Version in `pyproject.toml` and `src/qpprime/__init__.py`

## Key Concepts

### FinOps Policy Enforcement
- Budget guardrails and cost caps
- Required cost allocation tags: `team`, `environment`
- Carbon efficiency requirements
- Promotion gates with quality metrics
- All policies in `packages/policies/finops.rego`

### Telemetry & Unit Economics
- Real-time inference and training metrics
- Calibrated cost models (per-token pricing)
- Energy consumption and carbon footprint tracking
- DORA metrics support
- Resource monitor in `packages/telemetry/resource_monitor.py`

### Cloud Governance (Codex Guardrails)
- Multi-cloud controls matrix (see `CONTROLS_MATRIX.md`)
- OIDC-only authentication
- Drift-sentinel validators with daily checks
- Evidence artifacts in JSON, SARIF, Markdown, CSV
- Service Control Policies (SCPs) and Organization Policies

## Common Tasks

### Adding a New Feature
1. Create tests first (TDD approach)
2. Implement minimal code changes
3. Run tests: `python -m pytest tests/ -v`
4. Check security: `safety check --short-report`
5. Update documentation if needed
6. Submit PR with appropriate labels

### Modifying Policies
1. Edit `packages/policies/finops.rego`
2. Validate: `opa check packages/policies/finops.rego`
3. Test with conftest
4. Update tests in `tests/test_control_plane.py`
5. Verify in CI pipeline

### Adding Dependencies
1. Check for vulnerabilities: `safety check`
2. Add to `requirements.txt` or `pyproject.toml`
3. Update documentation
4. Test in CI pipeline
5. Generate SBOM if needed

## File Locations Reference

- **Main package**: `src/qpprime/`
- **Control Plane API**: `apps/control-plane/src/main.py`
- **Policies**: `packages/policies/finops.rego`
- **Telemetry**: `packages/telemetry/resource_monitor.py`
- **Tests**: `tests/`
- **Config**: `pyproject.toml`, `mkdocs.yml`
- **Docker**: `apps/control-plane/Dockerfile`, `infra/docker-compose.yml`
- **CI/CD**: `.github/workflows/`
- **Docs**: `docs/`

## Important Notes

1. **Never delete working tests** - Tests are critical for maintaining functionality
2. **Environment variables only** - No hardcoded secrets or configuration
3. **Fail-closed policies** - Security and cost policies must deny by default
4. **Multi-cloud support** - Consider Azure, AWS, and GCP when working on cloud features
5. **HMAC audit trails** - All events must be cryptographically signed
6. **Minimal changes** - Make surgical, focused changes to existing code
7. **Documentation updates** - Update docs when changing public APIs or features

## Getting Help

- **README.md**: Quick start guide
- **CONTRIBUTING.md**: Release process
- **SECURITY.md**: Security policies
- **CONTROLS_MATRIX.md**: Cloud governance controls
- **Component READMEs**: `apps/control-plane/README.md`, `infra/README.md`
- **Online docs**: https://Joedaddy66.github.io/spartan-resilience-framework/
