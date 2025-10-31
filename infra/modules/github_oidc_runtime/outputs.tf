output "service_account_hardening_effective_modes" {
  description = "Effective policy modes for service account hardening"
  value       = local.selected_profile
}

output "service_account_hardening_profile_summary_md" {
  description = "Markdown summary of the hardening profile"
  value       = local.profile_summary
}

output "harden_profile_selected" {
  description = "Selected hardening profile name"
  value       = var.harden_profile
}
