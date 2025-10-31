#!/bin/bash
# Validation helper script for GCP org policies
# Run after Terraform apply to validate policies are enforced

set -e

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
ORG_ID="${GCP_ORG_ID:-}"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID not set and no default project configured"
    exit 1
fi

if [ -z "$ORG_ID" ]; then
    echo "Warning: GCP_ORG_ID not set. Skipping org-level policy checks."
    exit 0
fi

echo "Validating GCP Organization Policies..."
echo "Organization: ${ORG_ID}"
echo "Project: ${PROJECT_ID}"
echo ""

FAILED=0

# Check each policy
check_policy() {
    local constraint=$1
    local expected=$2
    
    echo -n "Checking ${constraint}... "
    
    if gcloud org-policies describe "${constraint}" --organization="${ORG_ID}" --format=json 2>/dev/null | grep -q "${expected}"; then
        echo "✓ PASS"
    else
        echo "✗ FAIL"
        ((FAILED++))
    fi
}

check_policy "constraints/iam.disableServiceAccountKeyCreation" "enforce"
check_policy "iam.managed.disableServiceAccountKeyUpload" "enforce"
check_policy "iam.managed.disableServiceAccountApiKeyCreation" "enforce"
check_policy "constraints/storage.publicAccessPrevention" "enforced"

echo ""
if [ $FAILED -eq 0 ]; then
    echo "✓ All policies validated successfully"
    exit 0
else
    echo "✗ ${FAILED} policy check(s) failed"
    exit 1
fi
