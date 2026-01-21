terraform {
  required_version = ">= 1.0"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

# Module to generate service account hardening configuration
module "github_oidc_runtime" {
  source = "./modules/github_oidc_runtime"

  harden_profile         = var.harden_profile
  use_managed_constraint = var.use_managed_constraint
  project_id             = var.project_id
  org_id                 = var.org_id
  policy_scope           = var.policy_scope
}

# Human-readable Markdown attestation
resource "local_file" "policy_attestation_md" {
  content = join("\n", [
    "# Policy Attestation",
    "",
    module.github_oidc_runtime.service_account_hardening_profile_summary_md,
    "",
    format("- Profile: **%s**", module.github_oidc_runtime.harden_profile_selected),
    format("- Project: **%s**", var.project_id),
    var.org_id != "" ? format("- Org: **%s**", var.org_id) : "- Org: (none)",
    format("- Managed constraints: **%s**", var.use_managed_constraint),
    "- Terraform version: **>= 1.0**",
    format("- Timestamp (UTC): **%s**", timestamp()),
    format("- CI Commit SHA: **%s**", var.ci_commit_sha != "" ? var.ci_commit_sha : "(local)"),
  ])
  filename = "${var.attestation_dir}/policy-attestation.md"
}

# Machine-readable snapshot of modes
resource "local_file" "policy_effective_modes_json" {
  content  = jsonencode(module.github_oidc_runtime.service_account_hardening_effective_modes)
  filename = "${var.attestation_dir}/effective-modes.json"
}

# Post-apply validation hook
resource "null_resource" "validate_policies" {
  triggers = {
    modes_hash = sha1(jsonencode(module.github_oidc_runtime.service_account_hardening_effective_modes))
    profile    = module.github_oidc_runtime.harden_profile_selected
    scope      = var.policy_scope
    project    = var.project_id
    org        = var.org_id
    managed    = tostring(var.use_managed_constraint)
  }

  provisioner "local-exec" {
    command = join(" ", [
      "bash ${path.module}/validate_policies.sh",
      "--scope ${var.policy_scope}",
      "--project ${var.project_id}",
      var.org_id != "" ? "--org ${var.org_id}" : "",
      "--modes-json ${var.attestation_dir}/effective-modes.json",
      "--use-managed ${var.use_managed_constraint}"
    ])
  }

  depends_on = [
    local_file.policy_attestation_md,
    local_file.policy_effective_modes_json,
  ]
}
