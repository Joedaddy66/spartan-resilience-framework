<p align="center">
  <a href="https://pypi.org/project/qpprime/"><img alt="PyPI" src="https://img.shields.io/pypi/v/qpprime.svg"></a>
  <a href="https://pypi.org/project/qpprime/"><img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/qpprime.svg"></a>
  <a href="https://github.com/Joedaddy66/spartan-resilience-framework/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Joedaddy66/spartan-resilience-framework/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://Joedaddy66.github.io/spartan-resilience-framework/"><img alt="Docs" src="https://img.shields.io/badge/docs-mkdocs--material-informational"></a>
  <a href="https://github.com/Joedaddy66/spartan-resilience-framework/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/Joedaddy66/spartan-resilience-framework.svg"></a>
</p>

# Spartan Resilience Framework

A dual-civilization governance model for AI-human coexistence.

## Project Structure
- docs/: MkDocs site content
- slides/: Presentations (.pptx)
- src/: Source code / notebooks
- .github/workflows/: CI automation

## Security

This project implements comprehensive security measures:

- **Automated vulnerability scanning** with Safety and pip-audit
- **Static code analysis** with Bandit
- **Dependency monitoring** via Dependabot
- **Weekly security audits** via GitHub Actions
- **SBOM generation** for supply chain security

See [SECURITY.md](SECURITY.md) for details.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Command line interface
qpprime analyze --p 2 3 5 7
qpprime factor --p 13 17 19
qpprime table --p 2 3 5 --markdown
```

## License
See [LICENSE](LICENSE).
