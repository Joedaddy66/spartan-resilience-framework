# GitHub Labels

This directory contains the GitHub labels configuration for the repository.

## Files

- `labels.yml` - Defines all repository labels with colors and descriptions
- `workflows/sync-labels.yml` - Automatically syncs labels when `labels.yml` changes

## Labels Overview

The repository uses the following label categories:

### Dependabot Labels
- `dependencies` - Pull requests that update a dependency file
- `security` - Security-related updates and fixes
- `ci` - Continuous integration and GitHub Actions updates

### Development Labels
- `feature` - New feature or enhancement
- `enhancement` - Improvements to existing functionality
- `bug` - Something isn't working
- `fix` - Bug fixes
- `chore` - Maintenance tasks and housekeeping
- `refactor` - Code refactoring without functional changes
- `docs` - Documentation updates
- `build` - Build system and tooling updates

### Version Labels
- `major` - Major version bump (breaking changes)
- `minor` - Minor version bump (new features)
- `patch` - Patch version bump (bug fixes)

### Special Labels
- `skip-changelog` - Exclude from changelog

## How Labels Are Synced

1. Labels are defined in `.github/labels.yml`
2. When this file is updated and pushed to `main`, the `sync-labels` workflow automatically runs
3. The workflow uses [ghaction-github-labeler](https://github.com/crazy-max/ghaction-github-labeler) to sync labels
4. You can also manually trigger the sync from the Actions tab

## Manual Label Creation

If you need to manually create labels (e.g., for testing):

```bash
# Using GitHub CLI
gh label create "dependencies" --color "0366d6" --description "Pull requests that update a dependency file"
gh label create "security" --color "ee0701" --description "Security-related updates and fixes"
# ... etc
```

## References

- [Dependabot configuration](dependabot.yml)
- [Release Drafter configuration](release-drafter.yml)
