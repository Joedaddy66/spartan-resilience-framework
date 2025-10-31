# Define hardening profiles with policy modes
locals {
  # Profile definitions
  profiles = {
    baseline = {
      sa_key_creation                = "inherit"
      sa_key_upload                  = "inherit"
      sa_api_key_creation            = "inherit"
      prevent_privileged_basic_roles = "inherit"
      default_sa_auto_grants         = "inherit"
      sa_creation                    = "inherit"
    }
    moderate = {
      sa_key_creation                = "enforce"
      sa_key_upload                  = "enforce"
      sa_api_key_creation            = "enforce"
      prevent_privileged_basic_roles = "enforce"
      default_sa_auto_grants         = "off"
      sa_creation                    = "inherit"
    }
    strict = {
      sa_key_creation                = "enforce"
      sa_key_upload                  = "enforce"
      sa_api_key_creation            = "enforce"
      prevent_privileged_basic_roles = "enforce"
      default_sa_auto_grants         = "off"
      sa_creation                    = "enforce"
    }
  }

  # Selected profile
  selected_profile = local.profiles[var.harden_profile]

  # Summary text
  profile_summary = join("\n", [
    "## Service Account Hardening Profile",
    "",
    "### Policy Modes",
    format("- **Service Account Key Creation**: %s", local.selected_profile.sa_key_creation),
    format("- **Service Account Key Upload**: %s", local.selected_profile.sa_key_upload),
    format("- **Service Account API Key Creation**: %s", local.selected_profile.sa_api_key_creation),
    format("- **Prevent Privileged Basic Roles**: %s", local.selected_profile.prevent_privileged_basic_roles),
    format("- **Default SA Auto Grants**: %s", local.selected_profile.default_sa_auto_grants),
    format("- **Service Account Creation**: %s", local.selected_profile.sa_creation),
    "",
    "### Scope",
    format("- **Policy Scope**: %s", var.policy_scope),
    format("- **Constraint Type**: %s", var.use_managed_constraint ? "managed" : "legacy"),
  ])
}
