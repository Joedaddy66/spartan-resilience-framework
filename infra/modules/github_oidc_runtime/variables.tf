variable "harden_profile" {
  type        = string
  description = "Hardening profile: baseline, moderate, or strict"
}

variable "use_managed_constraint" {
  type        = bool
  description = "Use managed constraints"
}

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "org_id" {
  type        = string
  description = "GCP Organization ID"
}

variable "policy_scope" {
  type        = string
  description = "Policy scope: project or org"
}
