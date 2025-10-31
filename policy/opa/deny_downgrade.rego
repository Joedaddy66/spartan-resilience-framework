package terraform.deny

# Block any change that turns enforcement off or clears a rule on the org-policy constraints we care about.
# This is profile-agnostic: if a PR tries to weaken a constraint, we fail the gate.

default deny = false

constraints := {
  "constraints/iam.managed.disableServiceAccountKeyCreation",
  "constraints/iam.disableServiceAccountKeyCreation",
  "constraints/iam.managed.disableServiceAccountKeyUpload",
  "constraints/iam.disableServiceAccountKeyUpload",
  "constraints/iam.managed.disableServiceAccountApiKeyCreation",
  "constraints/iam.managed.preventPrivilegedBasicRolesForDefaultServiceAccounts",
  "constraints/iam.automaticIamGrantsForDefaultServiceAccounts",
  "constraints/iam.managed.disableServiceAccountCreation",
  "constraints/iam.disableServiceAccountCreation",
}

# Parse plan.json structure
resource_changes[r] {
  r := input.resource_changes[_]
  r.type == "google_org_policy_policy"
}

denies[msg] {
  r := resource_changes[_]
  # Planned values after the PR
  pv := r.change.after
  pv.name != null
  constraints[pv.name]
  # If rules absent or reset=true ⇒ effectively "inherit" (weakening) — block it
  (not pv.spec.rules[_].enforce) or pv.spec.reset == true
  msg := sprintf("Weakening org policy %q: rules missing/reset or enforce=false", [pv.name])
}

denies[msg] {
  r := resource_changes[_]
  r.type == "google_org_policy_policy"
  before := r.change.before
  after  := r.change.after
  constraints[after.name]
  # Explicit flip from enforce=true to enforce=false
  some i
  before.spec.rules[i].enforce == true
  after.spec.rules[i].enforce == false
  msg := sprintf("Turning OFF enforcement for %q", [after.name])
}

deny {
  count(denies) > 0
}
