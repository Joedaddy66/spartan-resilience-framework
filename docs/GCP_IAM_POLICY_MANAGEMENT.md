# GCP IAM Policy Management with Attestation

This implementation adds Terraform-based GCP IAM organization policy management with comprehensive attestation, validation, and drift detection capabilities.

## Overview

The system provides:

1. **Policy Management**: Terraform configuration for GCP IAM org policies with hardening profiles
2. **Attestation**: Machine-readable (JSON) and human-readable (Markdown) policy snapshots
3. **Validation**: Post-apply validation ensuring live policies match expected configuration
4. **Drift Detection**: Weekly scheduled checks for policy drift with GitHub issue creation
5. **PR Gates**: OPA policies prevent security policy downgrades in PRs

## Components

### Terraform Configuration

**Location**: `infra/`

- `variables.tf`: Input variables for project/org IDs, profiles, and attestation settings
- `main.tf`: Main configuration with attestation resources and validation hook
- `modules/github_oidc_runtime/`: Module that defines hardening profiles and effective policy modes

**Key Resources**:
- `local_file.policy_attestation_md`: Human-readable attestation in Markdown
- `local_file.policy_effective_modes_json`: Machine-readable policy modes in JSON
- `null_resource.validate_policies`: Post-apply validation hook

### Hardening Profiles

Three profiles available via `harden_profile` variable:

**baseline**: Minimal hardening
- All policies inherit from parent (no enforcement)

**moderate** (default):
- Service Account Key Creation: enforce
- Service Account Key Upload: enforce
- API Key Creation: enforce
- Prevent Privileged Basic Roles: enforce
- Default SA Auto Grants: off
- Service Account Creation: inherit

**strict**: Maximum hardening
- All moderate policies plus Service Account Creation: enforce

### Validation Script

**Location**: `infra/validate_policies.sh`

Bash script that:
1. Reads expected policy modes from JSON
2. Queries live GCP org policies via gcloud
3. Compares expected vs actual modes
4. Exits with code 42 on mismatch

**Usage**:
```bash
./validate_policies.sh \
  --scope project \
  --project YOUR_PROJECT_ID \
  --modes-json artifacts/effective-modes.json \
  --use-managed true
```

### GitHub Actions Workflows

**1. terraform.yml** - Main deployment workflow
- Triggers: Push to main, manual dispatch
- Actions:
  - Authenticates to GCP via OIDC
  - Runs `terraform apply` with CI commit SHA
  - Uploads attestation artifacts (365-day retention)
  - Validates live policies post-apply

**2. terraform-pr-gate.yml** - PR validation
- Triggers: PRs affecting infra/modules/workflows
- Actions:
  - Runs `terraform fmt -check`
  - Validates Terraform configuration
  - Runs TFLint
  - Generates plan.json
  - Runs OPA policy to block security downgrades
  - Shows policy attestation preview in PR summary

**3. drift-sentinel.yml** - Scheduled drift detection
- Triggers: Weekly (Mondays at 03:17 UTC), manual dispatch
- Actions:
  - Renders expected policy modes without applying changes
  - Validates live policies against expected
  - Creates/updates GitHub issue on mismatch
  - Uploads drift report and attestation as artifacts

### OPA Policy

**Location**: `policy/opa/deny_downgrade.rego`

Prevents PRs from weakening GCP org policy constraints:
- Blocks changes that set enforce=false
- Blocks changes that remove rules or reset policies
- Applies to all tracked IAM constraints

### CODEOWNERS

**Location**: `.github/CODEOWNERS`

Requires platform team review for:
- `infra/**`
- `modules/github-oidc-runtime/**`
- `.github/workflows/**`

## Usage

### Initial Setup

1. **Configure GCP authentication**:
   - Set up Workload Identity Federation
   - Configure GitHub Actions secrets:
     - `GCP_WIF_PROVIDER`
     - `GCP_SERVICE_ACCOUNT`
   - Configure GitHub variables:
     - `GCP_PROJECT_ID`

2. **Choose a profile** (optional):
   ```bash
   # In infra/variables.tf or via terraform.tfvars
   harden_profile = "moderate"  # or "baseline" or "strict"
   ```

3. **Run Terraform**:
   ```bash
   cd infra
   terraform init
   terraform plan
   terraform apply
   ```

### Generated Artifacts

After apply, find in `infra/artifacts/`:

**policy-attestation.md**:
```markdown
# Policy Attestation

## Service Account Hardening Profile
[...policy details...]

- Profile: **moderate**
- Project: **your-project-id**
- Terraform version: **1.9.5+**
- Timestamp (UTC): **2025-10-31T00:09:22Z**
- CI Commit SHA: **abc123**
```

**effective-modes.json**:
```json
{
  "sa_key_creation": "enforce",
  "sa_key_upload": "enforce",
  "sa_api_key_creation": "enforce",
  "prevent_privileged_basic_roles": "enforce",
  "default_sa_auto_grants": "off",
  "sa_creation": "inherit"
}
```

### Testing Changes

1. **Create a PR** changing policies in `infra/`
2. **terraform-pr-gate** workflow validates:
   - Terraform format and syntax
   - OPA policy prevents downgrades
   - Shows attestation preview in PR
3. **Merge** after approval
4. **terraform workflow** applies changes and validates

### Monitoring Drift

- **Automatic**: drift-sentinel runs weekly
- **Manual**: Trigger workflow dispatch in GitHub Actions
- **On mismatch**: GitHub issue created/updated with label `policy-drift`

## Security Considerations

1. **Least Privilege**: Service account should have minimal permissions
2. **Signed Commits**: Consider enabling for infra changes
3. **Branch Protection**: Enable required status checks
4. **Secret Management**: Never commit GCP credentials
5. **Audit Logs**: Review GCP audit logs for policy changes

## Future Enhancements

Potential additions:
- Cosign signing of attestations
- KMS-based attestation signatures
- Conftest checks on terraform plan
- Slack/PagerDuty notifications on drift
- Multi-cloud support (AWS, Azure)

## Troubleshooting

**Validation fails with "gcloud required"**:
- Ensure gcloud is installed in CI runner
- Check GCP authentication is configured

**Validation fails with mismatch**:
- Manual policy changes detected
- Review GCP console for unexpected changes
- Check drift-sentinel issue for details

**OPA policy blocks valid PR**:
- Review policy in `policy/opa/deny_downgrade.rego`
- Ensure PR is not weakening constraints
- Consider if constraint should be tracked

**Terraform apply fails**:
- Check GCP permissions
- Verify project/org IDs are correct
- Review Terraform state for conflicts
