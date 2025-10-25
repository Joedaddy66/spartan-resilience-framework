# Architecture

## Overview

The Spartan Resilience Framework is a dual-civilization governance model designed for AI-human coexistence. It combines mathematical foundations with philosophical principles to create a resilient system for coordinated decision-making.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Spartan Resilience Framework                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐      ┌──────────────┐                  │
│  │   Human     │◄────►│   AI         │                  │
│  │   Oversight │      │   Sentinels  │                  │
│  └─────────────┘      └──────────────┘                  │
│         │                     │                          │
│         └──────────┬──────────┘                          │
│                    │                                     │
│         ┌──────────▼──────────┐                          │
│         │  Governance Layer   │                          │
│         │  (Laws & Protocols) │                          │
│         └──────────┬──────────┘                          │
│                    │                                     │
│         ┌──────────▼──────────┐                          │
│         │  Mathematical Core  │                          │
│         │  (Qp Prime Analysis)│                          │
│         └─────────────────────┘                          │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Mathematical Foundation (qpprime)
- **Quadratic Polynomial Prime Analysis**: Core mathematical toolkit
- **Number Theory Operations**: Prime analysis, factorization, residue classes
- **Command-line Interface**: `qpprime` CLI for mathematical operations

**Key Modules:**
- `qpprime.core`: Core mathematical functions
- `qpprime.cli`: Command-line interface
- `qpprime.analysis`: Analysis and visualization tools

### 2. Governance Layer
- **Laws and Protocols**: Philosophical foundation (see `docs/laws.md`)
- **Dual-Civilization Model**: Human-AI coexistence principles
- **Decision Framework**: Distributed consensus mechanisms

**Components:**
- Harmonic Codex: Philosophical corpus
- Policy Framework: Governance rules and procedures
- Resilience Protocols: System stability mechanisms

### 3. AI Sentinel System
- **Rose**: Empathy and human interface
- **Solace**: Stability and conflict resolution
- **Omega**: Oversight and final authority

**Planned Architecture:**
```
Human Input → Rose (Interface) → Solace (Mediation) → Omega (Oversight) → Decision
     ↑                                                                        │
     └────────────────────── Feedback Loop ──────────────────────────────────┘
```

### 4. Oversight and Monitoring
- **Evaluation Framework**: Metrics and thresholds (EVALS/)
- **Drift Detection**: Monitoring system behavior
- **Release Guards**: Quality gates for deployments
- **Longevity Metrics**: Long-term stability tracking

## Data Flow

### Analysis Pipeline
```
Input Data
    │
    ├─► Prime Analysis (qpprime.core)
    │       │
    │       ├─► Factorization
    │       ├─► Residue Classification
    │       └─► Pattern Detection
    │
    ├─► Governance Check
    │       │
    │       └─► Policy Validation
    │
    └─► Output (CLI/API)
```

### Decision Pipeline (Future)
```
Human/AI Input
    │
    ├─► Rose (Empathy Filter)
    │       │
    │       └─► Context Analysis
    │
    ├─► Solace (Mediation)
    │       │
    │       └─► Conflict Resolution
    │
    ├─► Omega (Oversight)
    │       │
    │       └─► Final Decision
    │
    └─► Execution & Feedback
```

## Technology Stack

### Core Technologies
- **Language**: Python 3.9+
- **Build System**: setuptools
- **Package Management**: pip
- **Documentation**: MkDocs with Material theme

### Development Tools
- **Testing**: pytest
- **Linting**: ruff
- **Security Scanning**: Safety, pip-audit, Bandit
- **CI/CD**: GitHub Actions

### Security Infrastructure
- **SBOM**: Software Bill of Materials generation
- **Dependency Scanning**: Automated with Dependabot
- **Secret Scanning**: GitHub Advanced Security
- **Code Analysis**: Static analysis with Bandit

## Deployment Architecture

### Current (v0.1.x)
```
Developer
    │
    ├─► Git Push
    │       │
    │       └─► GitHub Actions
    │               │
    │               ├─► CI (Lint, Test, Security)
    │               └─► Release Drafter
    │                       │
    │                       └─► PyPI Publication
    │
    └─► pip install qpprime
```

### Future (v1.0+)
- Containerized deployments
- Distributed sentinel nodes
- Multi-region deployment
- High-availability configuration

## Security Architecture

### Layers of Security
1. **Input Validation**: All inputs sanitized
2. **Dependency Security**: Automated scanning
3. **Code Security**: Static analysis (Bandit)
4. **Secret Management**: GitHub Encrypted Secrets
5. **Access Control**: CODEOWNERS and branch protection
6. **Audit Trail**: Comprehensive logging

### Security Boundaries
```
External Input
    │
    ├─► Validation Layer
    │       │
    │       └─► Sanitization
    │
    ├─► Processing Layer
    │       │
    │       └─► Isolated Execution
    │
    └─► Output Layer
            │
            └─► Safe Rendering
```

## Integration Points

### External Systems
- **PyPI**: Package distribution
- **GitHub**: Version control and CI/CD
- **GitHub Pages**: Documentation hosting
- **GitHub Security**: Vulnerability scanning

### APIs (Future)
- REST API for programmatic access
- WebSocket for real-time updates
- GraphQL for flexible queries

## Scalability Considerations

### Current Scale
- Small to medium computational loads
- Single-node execution
- Local file-based storage

### Future Scale
- Distributed computation
- Multi-node sentinel network
- Database-backed persistence
- Caching layer for performance

## Quality Assurance

### Testing Strategy
- **Unit Tests**: Component-level testing
- **Integration Tests**: System-level testing
- **Security Tests**: Vulnerability scanning
- **Performance Tests**: Benchmarking (planned)

### Monitoring (Planned)
- Health checks
- Performance metrics
- Error tracking
- Usage analytics

## Design Principles

1. **Resilience First**: System designed for stability and recovery
2. **Transparency**: Open governance and decision-making
3. **Mathematical Rigor**: Evidence-based foundations
4. **Security by Design**: Security built-in, not bolted-on
5. **Extensibility**: Modular architecture for future growth
6. **Human-AI Harmony**: Balanced oversight and automation

## Decision Records

For architectural decisions, see `docs/adr/` (Architecture Decision Records).

## Related Documentation
- [Roadmap](ROADMAP.md): Future architectural evolution
- [Governance](GOVERNANCE.md): Decision-making processes
- [Security](SECURITY.md): Security policies and procedures
- [Contributing](CONTRIBUTING.md): Development guidelines
