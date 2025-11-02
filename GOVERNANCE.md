# Governance

## Overview

The Spartan Resilience Framework follows a transparent, community-driven governance model that balances rapid innovation with stability and security.

## Project Leadership

### Maintainers

**Lead Maintainer:**
- Joe Purvis (@Joedaddy66)

**Responsibilities:**
- Final decision authority on technical direction
- Release management and versioning
- Security incident response
- Community moderation

### Contributors

All contributors are valued members of the project. Recognition levels:
- **Core Contributors**: Regular contributors with demonstrated expertise
- **Community Contributors**: All who contribute code, documentation, or support
- **Emeritus Contributors**: Past contributors who remain in good standing

## Decision-Making Process

### Decision Hierarchy

1. **Routine Changes**: Documentation, tests, bug fixes
   - **Process**: PR review by any maintainer → Merge
   - **Required approvals**: 1

2. **Feature Additions**: New functionality, enhancements
   - **Process**: Issue discussion → Design review → Implementation → PR review
   - **Required approvals**: 1 maintainer

3. **Breaking Changes**: API changes, major refactors
   - **Process**: RFC → Community discussion → Design review → Implementation
   - **Required approvals**: Lead maintainer
   - **Notice**: Announced in CHANGELOG with migration guide

4. **Security Changes**: Security fixes, vulnerability patches
   - **Process**: Private disclosure → Patch development → Coordinated release
   - **Required approvals**: Lead maintainer
   - **Timeline**: 72-hour response, 30-day disclosure

5. **Governance Changes**: Changes to this document
   - **Process**: RFC → 2-week community feedback → Final decision
   - **Required approvals**: Lead maintainer
   - **Notice**: Announced to all contributors

### Consensus Model

We strive for **lazy consensus**:
- Proposals are accepted if no substantial objections within review period
- Objections must be technical and well-reasoned
- Maintainers have final say in case of unresolved disputes

## Contribution Process

### 1. Proposal
- **Small changes**: Open a PR directly
- **Large changes**: Open an issue for discussion first
- **Breaking changes**: RFC (Request for Comments) in discussions

### 2. Review
- Code review by maintainers
- Automated checks must pass (CI, security scans, tests)
- Documentation must be updated
- CHANGELOG must be updated for user-facing changes

### 3. Approval
- Minimum 1 approval from maintainer
- No outstanding change requests
- All CI checks passing

### 4. Merge
- Squash merge for feature branches
- Merge commit for releases
- Linear history maintained

## Code Ownership

### CODEOWNERS
Code ownership is defined in `.github/CODEOWNERS`:
- Specific files/directories require approval from designated owners
- Security-critical code requires additional review
- Tests can be owned independently from implementation

### Areas of Responsibility
- **Core Library**: Lead maintainer
- **CLI**: Lead maintainer
- **Documentation**: All maintainers
- **CI/CD**: Lead maintainer
- **Security**: Lead maintainer

## Release Process

### Versioning
We follow [Semantic Versioning 2.0.0](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality
- **PATCH**: Backward-compatible bug fixes

### Release Cycle
- **Patch releases**: As needed for bug fixes
- **Minor releases**: Monthly or as needed
- **Major releases**: When breaking changes are necessary

### Release Steps
1. Update version in `pyproject.toml` and `src/qpprime/__init__.py`
2. Update CHANGELOG.md with release notes
3. Create GitHub release using Release Drafter
4. Automated PyPI publication via CI/CD
5. Announcement in discussions

### Release Guards
Before release, verify:
- [ ] All tests passing
- [ ] Security scans clean
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] No known critical bugs
- [ ] Evaluation thresholds met (see RELEASE-GUARD.md)

## Dual-Key Merge Policy

For production releases and security-critical changes:
- **First key**: Code review and approval
- **Second key**: Required environment approval (production)
- Both keys required for deployment

Implementation:
- Branch protection on `main`
- Required reviewers for sensitive paths
- Environment protection for production deployments

## Community Guidelines

### Code of Conduct
All participants must follow our [Code of Conduct](CODE_OF_CONDUCT.md):
- Respectful and inclusive communication
- Constructive feedback
- Focus on project goals
- Zero tolerance for harassment

### Communication Channels
- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Q&A, ideas, announcements
- **Pull Requests**: Code contributions
- **Security**: Private disclosure via security@project

### Recognition
Contributors are recognized through:
- Commit attributions
- CHANGELOG mentions
- Contributors file
- Release notes

## Conflict Resolution

### Technical Disputes
1. Attempt consensus through discussion
2. Seek input from relevant experts
3. Maintainer makes final decision
4. Document decision rationale

### Code of Conduct Violations
1. Private warning for minor issues
2. Public warning for repeated issues
3. Temporary ban for serious violations
4. Permanent ban for severe violations

### Appeals
Contributors may appeal decisions by:
- Opening a discussion with lead maintainer
- Providing clear rationale
- Proposing alternative solution

## Security Governance

### Vulnerability Disclosure
Follow [SECURITY.md](SECURITY.md) for:
- Private disclosure process
- Response timeline
- Coordinated disclosure
- Security advisories

### Security Reviews
Required for:
- All dependency updates
- New external integrations
- Authentication/authorization changes
- Cryptographic implementations

### Security Incidents
Response process:
1. **Detection**: Automated scans or private disclosure
2. **Assessment**: Severity and impact analysis
3. **Patch**: Develop and test fix
4. **Release**: Coordinated security release
5. **Disclosure**: Public advisory after patch availability

## Evolution of Governance

This governance model may evolve as the project grows:
- Regular review (annually)
- Community feedback incorporated
- Scaling for larger contributor base
- Formal steering committee (if needed)

### Governance Changes
Proposed changes:
1. Open RFC in discussions
2. 2-week feedback period
3. Lead maintainer decision
4. Update this document
5. Announce to community

## Related Documents
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)

## Contact

For governance questions:
- GitHub Discussions
- Email: via GitHub profile
- Security issues: See [SECURITY.md](SECURITY.md)
