#!/usr/bin/env bash
set -euo pipefail

SCOPE="project"
PROJECT_ID=""
ORG_ID=""
MODES_JSON="artifacts/effective-modes.json"
USE_MANAGED="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) SCOPE="$2"; shift 2;;
    --project) PROJECT_ID="$2"; shift 2;;
    --org) ORG_ID="$2"; shift 2;;
    --modes-json) MODES_JSON="$2"; shift 2;;
    --use-managed) USE_MANAGED="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

command -v gcloud >/dev/null || { echo "gcloud required"; exit 1; }
command -v jq >/dev/null || { echo "jq required"; exit 1; }

if [[ "$SCOPE" == "org" && -z "$ORG_ID" ]]; then
  echo "scope=org requires --org"; exit 1
fi
if [[ "$SCOPE" == "project" && -z "$PROJECT_ID" ]]; then
  echo "scope=project requires --project"; exit 1
fi

flags=()
[[ "$SCOPE" == "project" ]] && flags+=(--project="$PROJECT_ID")
[[ "$SCOPE" == "org" ]] && flags+=(--organization="$ORG_ID")

# Choose constraint names
choose() {
  local managed="$1" legacy="$2"
  if [[ "$USE_MANAGED" == "true" ]]; then echo "$managed"; else echo "$legacy"; fi
}

C_KEY_CREATION="$(choose iam.managed.disableServiceAccountKeyCreation iam.disableServiceAccountKeyCreation)"
C_KEY_UPLOAD="$(choose iam.managed.disableServiceAccountKeyUpload iam.disableServiceAccountKeyUpload)"
C_API_KEY_CREATION="iam.managed.disableServiceAccountApiKeyCreation"
C_PREVENT_PRIV_BASIC="iam.managed.preventPrivilegedBasicRolesForDefaultServiceAccounts"
C_AUTO_GRANTS="iam.automaticIamGrantsForDefaultServiceAccounts"
C_SA_CREATION="$(choose iam.managed.disableServiceAccountCreation iam.disableServiceAccountCreation)"

declare -A CONSTRAINTS=(
  [sa_key_creation]="$C_KEY_CREATION"
  [sa_key_upload]="$C_KEY_UPLOAD"
  [sa_api_key_creation]="$C_API_KEY_CREATION"
  [prevent_privileged_basic_roles]="$C_PREVENT_PRIV_BASIC"
  [default_sa_auto_grants]="$C_AUTO_GRANTS"
  [sa_creation]="$C_SA_CREATION"
)

expected="$(cat "$MODES_JSON")"
fail=0

read_mode() {
  local constraint="$1"
  # If no local policy, describe may still return with empty spec; treat as inherit.
  local out
  if ! out="$(gcloud org-policies describe "constraints/${constraint}" "${flags[@]}" --format=json 2>/dev/null)"; then
    echo "inherit"; return
  fi
  local spec="$(jq -r '.spec // empty' <<<"$out")"
  [[ -z "$spec" ]] && { echo "inherit"; return; }
  local reset="$(jq -r '.spec.reset // false' <<<"$out")"
  [[ "$reset" == "true" ]] && { echo "inherit"; return; }
  local rules_len="$(jq -r '.spec.rules | length' <<<"$out")"
  [[ "$rules_len" == "0" ]] && { echo "inherit"; return; }
  local enforce="$(jq -r '.spec.rules[0].enforce // empty' <<<"$out")"
  if [[ "$enforce" == "true" ]]; then echo "enforce"
  elif [[ "$enforce" == "false" ]]; then echo "off"
  else echo "inherit"; fi
}

for key in "${!CONSTRAINTS[@]}"; do
  constraint="${CONSTRAINTS[$key]}"
  want="$(jq -r --arg k "$key" '.[$k]' <<<"$expected")"
  got="$(read_mode "$constraint")"
  printf "• %-35s want=%-8s got=%-8s (%s)\n" "$key" "$want" "$got" "$constraint"
  if [[ "$want" != "$got" ]]; then
    echo "  ✗ MISMATCH for $key"
    fail=1
  fi
done

if [[ "$fail" -ne 0 ]]; then
  echo "Validation failed: live org policies do not match expected modes." >&2
  exit 42
fi
echo "Validation succeeded: live org policies match expected modes."
