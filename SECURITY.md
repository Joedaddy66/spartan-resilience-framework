# Security Policy

## Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities to the project maintainers via:
- GitHub Security Advisories (preferred)
- Email to project maintainers

## Security Measures

This project implements several security measures:

### Dependency Security
- **Automated dependency scanning** with Safety and pip-audit
- **Dependabot** for automated security updates
- **Weekly security scans** via GitHub Actions
- **SBOM generation** for transparency

### Code Security  
- **Static analysis** with Bandit
- **Secret scanning** to prevent credential leaks
- **Code review** requirements for all changes

### Python Dependencies
We use the Python `requests` library (not the deprecated Node.js `request` package). 
We maintain:
- Minimum `requests >= 2.25.0` for security patches
- Regular dependency updates via Dependabot
- Vulnerability monitoring via Safety

### CI/CD Security
- **Security-first CI pipeline** with automated checks
- **Fail-fast** on critical vulnerabilities  
- **Artifact signing** and verification
- **Regular security audits**

## Secure Development Guidelines

1. **Dependencies**: Always use pinned, secure versions
2. **Secrets**: Never commit secrets to the repository  
3. **Updates**: Apply security patches promptly
4. **Review**: All changes require security review
5. **Monitoring**: Regular dependency and vulnerability scans
