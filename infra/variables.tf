variable "attestation_dir" {
  type        = string
  default     = "artifacts"
  description = "Directory to store policy attestation artifacts"
}

variable "ci_commit_sha" {
  type        = string
  default     = ""
  description = "Injected from CI (e.g., $GITHUB_SHA)"
}

variable "project_id" {
  type        = string
  description = "GCP Project ID"
  default     = ""
}

variable "org_id" {
  type        = string
  description = "GCP Organization ID (optional)"
  default     = ""
}

variable "policy_scope" {
  type        = string
  description = "Scope for org policies: 'project' or 'org'"
  default     = "project"
  validation {
    condition     = contains(["project", "org"], var.policy_scope)
    error_message = "policy_scope must be 'project' or 'org'"
  }
}

variable "use_managed_constraint" {
  type        = bool
  description = "Use managed constraints (true) or legacy constraints (false)"
  default     = true
}

variable "harden_profile" {
  type        = string
  description = "Hardening profile to apply: 'baseline', 'moderate', or 'strict'"
  default     = "moderate"
  validation {
    condition     = contains(["baseline", "moderate", "strict"], var.harden_profile)
    error_message = "harden_profile must be 'baseline', 'moderate', or 'strict'"
  }
}
