
        $badgeBlock = <p align="center">
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

## License
See [LICENSE](LICENSE)..Trim()
        # Find the last </a> tag and insert the new badge after it
        $lastAnchorIndex = $badgeBlock.LastIndexOf('</a>')
        $preBadge = $badgeBlock.Substring(0, $lastAnchorIndex + 4)
        $postBadge = $badgeBlock.Substring($lastAnchorIndex + 4)
        $preBadge + $newBadge + $postBadge
    
# Spartan Resilience Framework

A dual-civilization governance model for AI-human coexistence.

## Project Structure
- docs/: MkDocs site content
- slides/: Presentations (.pptx)
- src/: Source code / notebooks
- .github/workflows/: CI automation

## License
See [LICENSE](LICENSE).