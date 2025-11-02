# Release Guard

## Overview

The Release Guard ensures that only high-quality, secure, and stable code is deployed to production. This document defines the quality gates and criteria that must be met before any release.

## Purpose

- Prevent deployment of broken or insecure code
- Maintain system stability and reliability
- Ensure consistent quality standards
- Protect users from regressions

## Quality Gates

### 1. Code Quality Gate

**Required Checks:**
- [ ] All tests passing (100% pass rate)
- [ ] Code coverage ≥ target threshold (see below)
- [ ] No linting errors
- [ ] No type checking errors (if applicable)
- [ ] Code review completed and approved

**Coverage Thresholds:**
- Patch release (0.x.y): ≥80%
- Minor release (0.x.0): ≥85%
- Major release (x.0.0): ≥90%

### 2. Security Gate

**Required Checks:**
- [ ] No critical vulnerabilities (CVSS ≥9.0)
- [ ] No high vulnerabilities (CVSS ≥7.0) for major/minor releases
- [ ] Dependency scan clean (Safety, pip-audit)
- [ ] Static analysis clean (Bandit)
- [ ] Secret scanning clean
- [ ] SBOM generated and reviewed

**Vulnerability Response:**
- **Critical**: Must fix immediately, block all releases
- **High**: Fix before minor/major releases, can patch after
- **Medium**: Fix in next planned release
- **Low**: Fix when convenient

### 3. Performance Gate

**Required Checks:**
- [ ] No performance regressions >10%
- [ ] Memory usage within acceptable limits
- [ ] Response times meet SLA (when applicable)
- [ ] Benchmarks run and documented

**Baseline Metrics:**
- CLI commands: <100ms for simple operations
- Prime analysis: <1s for numbers <10^6
- Memory: <100MB for typical workloads

### 4. Documentation Gate

**Required Checks:**
- [ ] CHANGELOG.md updated with release notes
- [ ] API documentation updated (if API changes)
- [ ] User-facing documentation updated
- [ ] Migration guide provided (for breaking changes)
- [ ] README.md reflects current version

### 5. Drift Detection Gate

**What is Drift?**
Drift occurs when system behavior deviates from expected patterns over time. This is especially critical for AI systems.

**Monitoring:**
- [ ] Test results consistency (no unexpected flakiness)
- [ ] Output quality metrics stable
- [ ] Error rates within normal range
- [ ] User feedback sentiment unchanged

**Thresholds:**
- Test pass rate variance: <5%
- Error rate increase: <10%
- Performance degradation: <10%
- User satisfaction: No decrease

**Response to Drift:**
1. **Minor drift (<10%)**: Investigate and document
2. **Moderate drift (10-20%)**: Fix before release
3. **Major drift (>20%)**: Block release, root cause analysis

### 6. Longevity Metrics Gate

**Definition:**
Longevity metrics track the system's long-term stability and sustainability.

**Metrics:**
- [ ] Backward compatibility maintained (unless major version)
- [ ] Upgrade path provided
- [ ] Deprecation warnings in place (for future removals)
- [ ] Technical debt documented and managed

**Thresholds:**
- Breaking changes: Justified in CHANGELOG
- Deprecations: Minimum 2 minor versions notice
- Tech debt: No increase >10% per release
- Upgrade success rate: >95%

## Release Types and Requirements

### Patch Release (0.x.y)

**Purpose:** Bug fixes, security patches
**Requirements:**
- Gates 1, 2, 4 (minimum)
- Gate 3 for performance-related patches
- Fast-track security patches allowed with lead maintainer approval

### Minor Release (0.x.0)

**Purpose:** New features, enhancements
**Requirements:**
- All gates (1-6)
- Feature completeness verified
- User testing recommended

### Major Release (x.0.0)

**Purpose:** Breaking changes, major features
**Requirements:**
- All gates (1-6) with strictest thresholds
- Security audit completed
- Community preview period (recommended)
- Migration tools provided
- Extended testing period

## Pre-Release Checklist

Before creating a release:

### 1. Week Before
- [ ] Review open issues and PRs
- [ ] Identify release blockers
- [ ] Announce planned release date
- [ ] Prepare CHANGELOG draft

### 2. Days Before
- [ ] Run full test suite
- [ ] Run security scans
- [ ] Update documentation
- [ ] Review quality gates

### 3. Day Of
- [ ] Final quality gate verification
- [ ] Create git tag
- [ ] Trigger release workflow
- [ ] Monitor deployment
- [ ] Publish release notes

### 4. Post-Release
- [ ] Verify PyPI publication
- [ ] Test installation from PyPI
- [ ] Update GitHub release
- [ ] Announce release
- [ ] Monitor for issues

## Emergency Releases

For critical security vulnerabilities:

**Expedited Process:**
1. Private disclosure and assessment
2. Develop and test patch
3. Security-focused release (may skip some gates)
4. Coordinated public disclosure
5. Follow-up release for full compliance

**Required Gates:**
- Gate 1 (Code Quality) - tests only
- Gate 2 (Security) - vulnerability fix verified

## Automated Enforcement

Quality gates are enforced through:
- **GitHub Actions**: CI/CD pipeline
- **Branch Protection**: Required status checks
- **CODEOWNERS**: Required reviewers
- **Environment Protection**: Production approval gates

**Configuration:**
See `.github/workflows/ci.yml` and `.github/workflows/release.yml`

## Dual-Key Merge Policy

Critical changes require two approvals:
- **First Key**: Code review approval
- **Second Key**: Environment approval (for production)

**Implemented via:**
- Required reviewers (CODEOWNERS)
- Environment protection rules
- Mandatory approvals before merge

## Monitoring and Metrics

**Dashboard Metrics:**
- Release frequency
- Time to release
- Gate pass/fail rates
- Regression frequency
- Security incident count

**Alerts:**
- Gate failures
- Security vulnerabilities
- Performance degradation
- Drift detection

## Continuous Improvement

This Release Guard is reviewed and updated:
- After each major release
- When gates are frequently failing or passing trivially
- When new risks are identified
- Based on post-mortem learnings

## Related Documents
- [EVALS/README.md](EVALS/README.md): Evaluation framework
- [GOVERNANCE.md](GOVERNANCE.md): Decision-making process
- [SECURITY.md](SECURITY.md): Security policies
- [CONTRIBUTING.md](CONTRIBUTING.md): Development guidelines
- [.github/workflows/](,github/workflows/): CI/CD configuration

## Contact

For questions about release gates:
- Open an issue with label `release-process`
- Contact lead maintainer for critical issues
- See [SUPPORT.md](SUPPORT.md) for general support
