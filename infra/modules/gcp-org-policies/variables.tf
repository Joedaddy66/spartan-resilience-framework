variable "organization_id" {
  description = "GCP Organization ID (e.g., 'organizations/123456789')"
  type        = string
}

variable "harden_service_accounts_profile" {
  description = "Service account hardening profile: STRICT, DEFAULT, or CUSTOM"
  type        = string
  default     = "DEFAULT"

  validation {
    condition     = contains(["STRICT", "DEFAULT", "CUSTOM"], var.harden_service_accounts_profile)
    error_message = "Profile must be one of: STRICT, DEFAULT, CUSTOM"
  }
}

variable "disable_default_sa_creation" {
  description = "Whether to disable automatic IAM grants for default service accounts"
  type        = bool
  default     = false
}

variable "harden_service_accounts" {
  description = "Whether to enable additional service account hardening policies"
  type        = bool
  default     = true
}
