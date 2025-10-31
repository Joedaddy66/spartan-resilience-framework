output "org_policies_applied" {
  description = "List of organization policies applied"
  value = concat(
    var.organization_id != "" ? [
      "iam.disableServiceAccountKeyCreation",
      "iam.managed.disableServiceAccountKeyUpload",
      "iam.managed.disableServiceAccountApiKeyCreation",
      "storage.publicAccessPrevention"
    ] : [],
    var.organization_id != "" && var.disable_default_sa_creation ? ["iam.automaticIamGrantsForDefaultServiceAccounts"] : [],
    var.organization_id != "" && var.harden_service_accounts ? ["iam.serviceAccountKeyExpiryHours"] : []
  )
}
