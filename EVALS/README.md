# Evaluation Framework

This directory contains reproducible evaluations and quality thresholds for the Spartan Resilience Framework.

## Overview

Evaluations ensure that each release meets quality, performance, and safety standards before deployment.

## Evaluation Categories

### 1. Mathematical Correctness
- Prime analysis accuracy
- Factorization correctness
- Residue class validation
- Edge case handling

### 2. Performance Benchmarks
- Computation time for various input sizes
- Memory usage profiles
- CLI response times
- API latency (when available)

### 3. Security Assessments
- Vulnerability scan results
- Dependency health checks
- Code analysis scores
- Penetration testing results

### 4. AI Safety (Future)
- Decision consistency
- Bias detection
- Adversarial robustness
- Explainability metrics

## Threshold Requirements

### Release Thresholds

**Patch Release (0.x.y):**
- [ ] All unit tests passing (100%)
- [ ] No high or critical security vulnerabilities
- [ ] No performance regressions >10%
- [ ] Documentation updated

**Minor Release (0.x.0):**
- [ ] Test coverage ≥80%
- [ ] No medium+ security vulnerabilities
- [ ] Performance benchmarks within 5% of baseline
- [ ] API documentation complete
- [ ] User-facing features documented

**Major Release (x.0.0):**
- [ ] Test coverage ≥90%
- [ ] Zero security vulnerabilities
- [ ] Performance meets or exceeds previous major version
- [ ] Complete documentation suite
- [ ] Migration guide provided
- [ ] Security audit completed

### AI Safety Thresholds (Future)

**Rose (Empathy Module):**
- Sentiment accuracy >85%
- Cultural sensitivity score >90%
- False positive rate <5%
- Response time <500ms

**Solace (Mediation Module):**
- Conflict resolution success rate >80%
- Fairness score >95%
- Unintended bias <3%
- Consensus time <2s

**Omega (Oversight Module):**
- Decision accuracy >95%
- Override precision >98%
- Audit completeness 100%
- Response time <100ms

## Running Evaluations

### Prerequisites
```bash
pip install -e .[dev]
```

### Run All Tests
```bash
pytest tests/ -v --cov=qpprime --cov-report=term-missing
```

### Performance Benchmarks
```bash
# TODO: Add benchmark runner
# python EVALS/run_benchmarks.py
```

### Security Scans
```bash
# Dependency vulnerabilities
safety check
pip-audit

# Static code analysis
bandit -r src/

# SBOM generation
cyclonedx-py -o sbom.json
```

## Evaluation Reports

Evaluation reports are stored in `EVALS/reports/` with the format:
```
EVALS/reports/
├── v0.1.0/
│   ├── tests.json
│   ├── benchmarks.json
│   ├── security.json
│   └── summary.md
├── v0.1.1/
│   └── ...
```

## Adding New Evaluations

1. Create evaluation script in `EVALS/scripts/`
2. Define success criteria and thresholds
3. Add to CI/CD pipeline if applicable
4. Document in this README
5. Update release checklist

## Continuous Monitoring

Between releases, we monitor:
- Security advisories (GitHub Dependabot)
- Dependency updates (weekly scans)
- Performance trends (profiling on main branch)
- Test stability (flaky test detection)

## Related Documents
- [RELEASE-GUARD.md](../RELEASE-GUARD.md): Release quality gates
- [CONTRIBUTING.md](../CONTRIBUTING.md): Development guidelines
- [SECURITY.md](../SECURITY.md): Security policies
- [.github/workflows/ci.yml](../.github/workflows/ci.yml): CI configuration
