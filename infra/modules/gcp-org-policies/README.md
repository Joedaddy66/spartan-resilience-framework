# GCP Organization Policies Module

This Terraform module applies organization-level policies for GCP to enforce Codex Controls Matrix v0.9.1.

## Features

- Disables service account key creation, upload, and API key creation (Control A1)
- Enforces storage public access prevention (Control A2)
- Optional: Disables automatic IAM grants for default service accounts
- Optional: Enforces service account key expiry

## Usage

```hcl
module "gcp_org_policies" {
  source = "./modules/gcp-org-policies"

  organization_id                = "organizations/123456789"
  harden_service_accounts_profile = "STRICT"
  disable_default_sa_creation    = true
  harden_service_accounts        = true
}
```

## Profiles

### STRICT
- Disables all service account key operations
- Enforces storage public access prevention
- Disables default service account automatic grants
- Enforces key expiry (90 days)

### DEFAULT
- Disables service account key creation/upload
- Enforces storage public access prevention

### CUSTOM
- Same as DEFAULT, but allows overriding individual settings

## Control Mapping

- **A1: No Long-Term Credentials** - Disables SA key creation/upload/API keys
- **A2: Storage Public Access** - Enforces public access prevention
- **A8: RBAC Least Privilege** - Restricts default SA privileges

## Requirements

- Organization-level permissions (`orgpolicy.policy.set`)
- Google Cloud provider ~> 5.0
- Terraform >= 1.0
