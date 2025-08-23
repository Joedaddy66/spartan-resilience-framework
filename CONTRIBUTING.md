## Release Process

We use **Release Drafter** to maintain a draft release from merged PRs.

1. Open PRs with clear titles and apply labels (e.g., `feature`, `bug`, `docs`).
2. Release Drafter updates the draft automatically.
3. When ready, **Publish** the draft release — this creates a tag like `v0.1.2`.
4. Our GitHub Action publishes to **PyPI** on tag (token-based workflow).
5. Bump `__version__` in `src/qpprime/__init__.py` and `version` in `pyproject.toml` for the next cycle.
