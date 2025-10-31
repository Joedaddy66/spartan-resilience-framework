# Terraform Offline Validate Action

A reusable composite GitHub Action that pre-warms Terraform provider cache and validates configuration offline, safe for environments with egress firewalls.

## Problem Statement

When running Terraform in environments with strict egress firewall rules, you may encounter network connectivity issues:

1. **checkpoint-api.hashicorp.com** - Terraform's version check
2. **registry.terraform.io / releases.hashicorp.com** - Provider downloads
3. **metadata.google.internal** - Google client libraries probing GCE metadata (when not authenticated)

This action solves these issues by:
- Disabling Terraform checkpoint calls via `CHECKPOINT_DISABLE=1`
- Pre-warming the provider cache before firewall enforcement
- Setting up proper cloud authentication to avoid metadata probes
- Running validation in offline mode using cached providers

## Usage

### Basic Usage (No Cloud Authentication)

```yaml
- uses: ./.github/actions/tf-offline-validate
  with:
    terraform_version: '1.9.5'
    working_directory: 'infra'
```

### With GCP Authentication

```yaml
- uses: ./.github/actions/tf-offline-validate
  with:
    terraform_version: '1.9.5'
    working_directory: 'infra'
    gcp_workload_identity_provider: ${{ secrets.GCP_WIF_PROVIDER }}
    gcp_service_account: ${{ secrets.GCP_WIF_SA }}
```

### With AWS Authentication

```yaml
- uses: ./.github/actions/tf-offline-validate
  with:
    terraform_version: '1.9.5'
    working_directory: 'infra'
    aws_role_arn: ${{ secrets.AWS_ROLE_ARN }}
    aws_region: 'us-east-1'
```

### With Azure Authentication

```yaml
- uses: ./.github/actions/tf-offline-validate
  with:
    terraform_version: '1.9.5'
    working_directory: 'infra'
    azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
    azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
    azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### Multi-Cloud Example

```yaml
- uses: ./.github/actions/tf-offline-validate
  with:
    terraform_version: '1.9.5'
    working_directory: 'infra'
    gcp_workload_identity_provider: ${{ secrets.GCP_WIF_PROVIDER }}
    gcp_service_account: ${{ secrets.GCP_WIF_SA }}
    aws_role_arn: ${{ secrets.AWS_ROLE_ARN }}
    aws_region: 'us-east-1'
    azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
    azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
    azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `terraform_version` | Terraform version to use | No | `1.9.5` |
| `working_directory` | Directory containing Terraform configuration | No | `infra` |
| `gcp_workload_identity_provider` | GCP Workload Identity Provider | No | `''` |
| `gcp_service_account` | GCP Service Account | No | `''` |
| `aws_role_arn` | AWS IAM Role ARN | No | `''` |
| `aws_region` | AWS Region | No | `us-east-1` |
| `azure_client_id` | Azure Client ID | No | `''` |
| `azure_tenant_id` | Azure Tenant ID | No | `''` |
| `azure_subscription_id` | Azure Subscription ID | No | `''` |

## Outputs

| Output | Description |
|--------|-------------|
| `validation_result` | Result of terraform validate command (`success` or error) |

## How It Works

1. **Setup Phase (Pre-Firewall)**
   - Installs Terraform
   - Authenticates to cloud providers (if credentials provided)
   - Pre-warms provider cache with `terraform init -backend=false -upgrade`
   - Caches downloaded providers for future runs

2. **Validation Phase (Offline)**
   - Sets environment variables:
     - `CHECKPOINT_DISABLE=1` - Disables checkpoint-api.hashicorp.com calls
     - `TF_IN_AUTOMATION=true` - Marks as CI environment
     - `TF_PLUGIN_CACHE_DIR` - Uses cached providers
     - `NO_GCE_CHECK=true` - Skips GCE metadata probe
     - `CLOUDSDK_CORE_CHECK_GCE_METADATA=0` - Disables Cloud SDK metadata check
   - Runs `terraform init -backend=false -get=false` (uses cache, no downloads)
   - Runs `terraform validate`

## Local/CLI Equivalent

To replicate this behavior locally:

```bash
# 1) Disable network calls & set cache
export CHECKPOINT_DISABLE=1
export TF_IN_AUTOMATION=true
export TF_PLUGIN_CACHE_DIR="$PWD/.tf-cache"
printf 'plugin_cache_dir = "%s"\n' "$TF_PLUGIN_CACHE_DIR" > ~/.terraformrc

# 2) (One-time online) prefetch providers
terraform -chdir=infra init -backend=false -upgrade

# 3) (Offline) validate
terraform -chdir=infra init -backend=false -get=false
terraform -chdir=infra validate
```

## Firewall Allowlist (Alternative Approach)

If you prefer to allowlist instead of using offline mode:

**Required domains:**
- `checkpoint-api.hashicorp.com` (or set `CHECKPOINT_DISABLE=1`)
- `registry.terraform.io`
- `releases.hashicorp.com`

**Do NOT allowlist:**
- `metadata.google.internal` - GCE-only endpoint; provide credentials instead

## Integration with Existing Workflows

Add to your workflow before enabling firewall rules:

```yaml
jobs:
  terraform-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: ./.github/actions/tf-offline-validate
        with:
          terraform_version: '1.9.5'
          working_directory: 'infra'
          gcp_workload_identity_provider: ${{ secrets.GCP_WIF_PROVIDER }}
          gcp_service_account: ${{ secrets.GCP_WIF_SA }}
      
      # Enable firewall rules here (if applicable)
      # ... rest of workflow
```

## Benefits

✅ **Firewall-safe** - No network calls after initial provider download  
✅ **Fast** - Cached providers speed up subsequent runs  
✅ **Multi-cloud** - Supports AWS, Azure, and GCP authentication  
✅ **Reusable** - Composite action usable across repositories  
✅ **No allowlist required** - Offline mode eliminates firewall exceptions  

## Credits

Based on the suggestion by @Joedaddy66 for handling Terraform in egress-restricted environments.
