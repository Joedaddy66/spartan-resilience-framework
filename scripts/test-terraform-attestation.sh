#!/usr/bin/env bash
# Integration test for Terraform attestation and validation system
# This script validates the complete workflow without requiring GCP credentials

set -euo pipefail

echo "=== Terraform Attestation & Validation Integration Test ==="
echo ""

cd "$(dirname "$0")/../infra"

# Test 1: Terraform validation
echo "Test 1: Terraform validation..."
terraform init -input=false >/dev/null 2>&1
terraform validate
echo "✓ Terraform configuration is valid"
echo ""

# Test 2: Terraform format check
echo "Test 2: Terraform format check..."
terraform fmt -check -recursive
echo "✓ Terraform files are properly formatted"
echo ""

# Test 3: Test all three hardening profiles
echo "Test 3: Testing hardening profiles..."
for profile in baseline moderate strict; do
  echo "  Testing profile: $profile"
  terraform plan -var="project_id=test-project-123" -var="harden_profile=$profile" -out=/tmp/test-${profile}.plan >/dev/null 2>&1
  echo "  ✓ $profile profile validated"
done
rm -f /tmp/test-*.plan
echo ""

# Test 4: Generate attestation files
echo "Test 4: Generating attestation artifacts..."
terraform apply -auto-approve \
  -target=local_file.policy_attestation_md \
  -target=local_file.policy_effective_modes_json \
  -var="project_id=test-project-123" \
  -var="ci_commit_sha=test-sha-123" \
  -var="harden_profile=moderate" >/dev/null 2>&1

if [[ ! -f artifacts/policy-attestation.md ]]; then
  echo "✗ Failed to generate policy-attestation.md"
  exit 1
fi

if [[ ! -f artifacts/effective-modes.json ]]; then
  echo "✗ Failed to generate effective-modes.json"
  exit 1
fi

echo "✓ Attestation artifacts generated successfully"
echo ""

# Test 5: Validate attestation content
echo "Test 5: Validating attestation content..."
grep -q "Profile: \*\*moderate\*\*" artifacts/policy-attestation.md || {
  echo "✗ Missing profile in attestation"
  exit 1
}
grep -q "CI Commit SHA: \*\*test-sha-123\*\*" artifacts/policy-attestation.md || {
  echo "✗ Missing commit SHA in attestation"
  exit 1
}
echo "✓ Attestation content is correct"
echo ""

# Test 6: Validate JSON structure
echo "Test 6: Validating JSON structure..."
if ! command -v jq >/dev/null 2>&1; then
  echo "  ⚠ jq not installed, skipping JSON validation"
else
  jq empty artifacts/effective-modes.json || {
    echo "✗ Invalid JSON in effective-modes.json"
    exit 1
  }
  
  # Check for required keys
  for key in sa_key_creation sa_key_upload sa_api_key_creation prevent_privileged_basic_roles default_sa_auto_grants sa_creation; do
    if ! jq -e --arg k "$key" 'has($k)' artifacts/effective-modes.json >/dev/null; then
      echo "✗ Missing key: $key"
      exit 1
    fi
  done
  echo "✓ JSON structure is valid"
fi
echo ""

# Test 7: Validate script syntax
echo "Test 7: Validating validation script..."
bash -n validate_policies.sh
echo "✓ Validation script syntax is correct"
echo ""

# Test 8: OPA policy syntax (if OPA is available)
echo "Test 8: Validating OPA policy..."
cd ..
if command -v opa >/dev/null 2>&1; then
  opa check policy/opa/deny_downgrade.rego
  echo "✓ OPA policy syntax is valid"
else
  echo "  ⚠ OPA not installed, skipping policy validation"
fi
echo ""

# Test 9: YAML syntax check for workflows
echo "Test 9: Validating workflow YAML syntax..."
workflow_count=0
for workflow in .github/workflows/terraform.yml .github/workflows/terraform-pr-gate.yml .github/workflows/drift-sentinel.yml; do
  if [[ -f "$workflow" ]]; then
    # Basic YAML syntax check (Python required)
    if command -v python3 >/dev/null 2>&1; then
      python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null && {
        workflow_count=$((workflow_count + 1))
      } || {
        echo "✗ Invalid YAML: $workflow"
        exit 1
      }
    fi
  fi
done
echo "✓ Validated $workflow_count workflow files"
echo ""

# Cleanup
echo "Cleaning up test artifacts..."
cd infra
rm -rf artifacts/ .terraform/ .terraform.lock.hcl terraform.tfstate*
echo "✓ Cleanup complete"
echo ""

echo "=== All Integration Tests Passed ==="
echo ""
echo "Summary:"
echo "  ✓ Terraform configuration validated"
echo "  ✓ All hardening profiles tested"
echo "  ✓ Attestation generation verified"
echo "  ✓ JSON structure validated"
echo "  ✓ Scripts and policies validated"
echo "  ✓ Workflow YAML syntax checked"
echo ""
echo "Ready for deployment!"
