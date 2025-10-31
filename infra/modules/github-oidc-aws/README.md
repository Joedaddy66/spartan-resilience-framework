# GitHub OIDC AWS Module

This Terraform module creates an AWS IAM role with OIDC federation for GitHub Actions.

## Features

- Creates GitHub OIDC provider in AWS
- IAM role with trust policy for GitHub Actions
- Configurable repository subjects for fine-grained access control
- Support for managed and inline policies
- Enforces least-privilege access patterns

## Usage

```hcl
module "github_oidc" {
  source = "./modules/github-oidc-aws"

  role_name = "github-actions-drift-sentinel"
  
  github_repo_subjects = [
    "repo:Joedaddy66/spartan-resilience-framework:*"
  ]
  
  policy_arns = [
    "arn:aws:iam::aws:policy/ReadOnlyAccess"
  ]
  
  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

## Outputs

- `role_arn` - ARN of the created IAM role (use in GitHub Actions with `aws-actions/configure-aws-credentials`)
- `role_name` - Name of the IAM role
- `oidc_provider_arn` - ARN of the GitHub OIDC provider

## Control A1: No Long-Term Credentials

This module supports Control A1 by:
- Enabling OIDC-only authentication (no long-term access keys)
- Trust policy restricted to specific GitHub repositories
- Session duration limits
