#!/bin/bash
set -e

# GCP Drift Sentinel Validator
# Validates GCP guardrails for Codex Controls Matrix v0.9.1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="${SCRIPT_DIR}/../artifacts"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results tracking
declare -a ERRORS=()
declare -a WARNINGS=()
declare -a PASSED=()

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ERRORS+=("$1")
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS+=("$1")
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED+=("$1")
}

log_info() {
    echo "[INFO] $1"
}

# Ensure gcloud is available
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found. Please install it."
    exit 1
fi

# Check gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    log_error "Not authenticated with gcloud. Run 'gcloud auth login' first."
    exit 1
fi

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
ORG_ID=${GCP_ORG_ID:-""}

if [ -z "$PROJECT_ID" ]; then
    log_error "GCP_PROJECT_ID not set and no default project configured"
    exit 1
fi

log_info "Running GCP Drift Sentinel"
log_info "Project: ${PROJECT_ID}"
log_info "Organization ID: ${ORG_ID:-N/A}"
log_info "Timestamp: ${TIMESTAMP}"
echo ""

# Create artifacts directory
mkdir -p "${ARTIFACTS_DIR}"

declare -a ORG_POLICIES=()

# A1: Check for service account key creation restrictions
log_info "Checking A1: No Long-Term Credentials (SA Key Restrictions)..."

if [ -n "$ORG_ID" ]; then
    # Check org-level policies
    SA_KEY_CREATION=$(gcloud org-policies describe constraints/iam.disableServiceAccountKeyCreation --organization="$ORG_ID" --format=json 2>/dev/null || echo '{}')
    SA_KEY_UPLOAD=$(gcloud org-policies describe iam.managed.disableServiceAccountKeyUpload --organization="$ORG_ID" --format=json 2>/dev/null || echo '{}')
    API_KEY_CREATION=$(gcloud org-policies describe iam.managed.disableServiceAccountApiKeyCreation --organization="$ORG_ID" --format=json 2>/dev/null || echo '{}')
    
    # Check if enforced
    if echo "$SA_KEY_CREATION" | jq -e '.spec.rules[0].enforce == true' &> /dev/null; then
        log_pass "Org policy iam.disableServiceAccountKeyCreation is enforced"
        ORG_POLICIES+=('{"constraint":"iam.disableServiceAccountKeyCreation","status":"enforced"}')
    else
        log_warning "Org policy iam.disableServiceAccountKeyCreation is not enforced"
        ORG_POLICIES+=('{"constraint":"iam.disableServiceAccountKeyCreation","status":"not-enforced"}')
    fi
    
    if echo "$SA_KEY_UPLOAD" | jq -e '.spec.rules[0].enforce == true' &> /dev/null; then
        log_pass "Org policy iam.managed.disableServiceAccountKeyUpload is enforced"
        ORG_POLICIES+=('{"constraint":"iam.managed.disableServiceAccountKeyUpload","status":"enforced"}')
    else
        log_warning "Org policy iam.managed.disableServiceAccountKeyUpload is not enforced"
        ORG_POLICIES+=('{"constraint":"iam.managed.disableServiceAccountKeyUpload","status":"not-enforced"}')
    fi
else
    log_info "No organization ID provided, skipping org-level policy checks"
fi

# A2: Check storage public access prevention
log_info "Checking A2: Storage Public Access Prevention..."

if [ -n "$ORG_ID" ]; then
    STORAGE_PUBLIC_ACCESS=$(gcloud org-policies describe constraints/storage.publicAccessPrevention --organization="$ORG_ID" --format=json 2>/dev/null || echo '{}')
    
    if echo "$STORAGE_PUBLIC_ACCESS" | jq -e '.spec.rules[0].values.allowedValues[0] == "enforced"' &> /dev/null; then
        log_pass "Org policy storage.publicAccessPrevention is enforced"
        ORG_POLICIES+=('{"constraint":"storage.publicAccessPrevention","status":"enforced"}')
    else
        log_warning "Org policy storage.publicAccessPrevention is not enforced"
        ORG_POLICIES+=('{"constraint":"storage.publicAccessPrevention","status":"not-enforced"}')
    fi
else
    # Check project-level buckets
    BUCKETS=$(gcloud storage buckets list --project="$PROJECT_ID" --format=json 2>/dev/null || echo '[]')
    NONCOMPLIANT_BUCKETS=0
    
    while IFS= read -r bucket; do
        BUCKET_NAME=$(echo "$bucket" | jq -r '.name')
        UNIFORM_ACCESS=$(echo "$bucket" | jq -r '.iamConfiguration.uniformBucketLevelAccess.enabled')
        
        if [ "$UNIFORM_ACCESS" != "true" ]; then
            log_warning "Bucket ${BUCKET_NAME} does not have uniform bucket-level access enabled"
            ((NONCOMPLIANT_BUCKETS++))
        fi
    done < <(echo "$BUCKETS" | jq -c '.[]')
    
    if [ $NONCOMPLIANT_BUCKETS -eq 0 ]; then
        log_pass "All buckets have uniform bucket-level access enabled"
    else
        log_warning "${NONCOMPLIANT_BUCKETS} bucket(s) do not have uniform bucket-level access"
    fi
fi

# A8: Check default service account restrictions
log_info "Checking A8: Default Service Account Restrictions..."

# Check if default compute SA is being used
DEFAULT_SA="${PROJECT_ID}-compute@developer.gserviceaccount.com"
SA_BINDINGS=$(gcloud projects get-iam-policy "$PROJECT_ID" --format=json 2>/dev/null || echo '{}')

if echo "$SA_BINDINGS" | jq -e ".bindings[] | select(.members[] | contains(\"serviceAccount:${DEFAULT_SA}\")) | select(.role | contains(\"Editor\") or contains(\"Owner\"))" &> /dev/null; then
    log_warning "Default compute service account has Editor or Owner role"
else
    log_pass "Default compute service account does not have privileged roles"
fi

# Generate summary
echo ""
log_info "=== Validation Summary ==="
echo "Passed: ${#PASSED[@]}"
echo "Warnings: ${#WARNINGS[@]}"
echo "Errors: ${#ERRORS[@]}"

# Generate JSON attestation
cat > "${ARTIFACTS_DIR}/gcp-org-policy-attestation.json" <<EOF
{
  "version": "0.9.1",
  "timestamp": "${TIMESTAMP}",
  "project_id": "${PROJECT_ID}",
  "organization_id": "${ORG_ID}",
  "org_policies": [$(IFS=,; echo "${ORG_POLICIES[*]}")],
  "summary": {
    "passed": ${#PASSED[@]},
    "warnings": ${#WARNINGS[@]},
    "errors": ${#ERRORS[@]}
  }
}
EOF

# Generate SARIF
cat > "${ARTIFACTS_DIR}/gcp-org-policy-attestation.sarif" <<EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "GCP Drift Sentinel",
          "version": "0.9.1",
          "informationUri": "https://github.com/Joedaddy66/spartan-resilience-framework"
        }
      },
      "results": []
    }
  ]
}
EOF

# Generate Markdown report
cat > "${ARTIFACTS_DIR}/policy-attestation.md" <<EOF
# GCP Organization Policy Attestation Report

**Version:** 0.9.1  
**Timestamp:** ${TIMESTAMP}  
**Project:** ${PROJECT_ID}  
**Organization:** ${ORG_ID:-N/A}

## Summary

- ✅ Passed: ${#PASSED[@]}
- ⚠️  Warnings: ${#WARNINGS[@]}
- ❌ Errors: ${#ERRORS[@]}

## Org Policy Status

EOF

for policy in "${ORG_POLICIES[@]}"; do
    CONSTRAINT=$(echo "$policy" | jq -r '.constraint')
    STATUS=$(echo "$policy" | jq -r '.status')
    if [ "$STATUS" = "enforced" ]; then
        echo "### ${CONSTRAINT}" >> "${ARTIFACTS_DIR}/policy-attestation.md"
        echo "Status: ✅ Enforced" >> "${ARTIFACTS_DIR}/policy-attestation.md"
        echo "" >> "${ARTIFACTS_DIR}/policy-attestation.md"
    else
        echo "### ${CONSTRAINT}" >> "${ARTIFACTS_DIR}/policy-attestation.md"
        echo "Status: ⚠️ Not Enforced" >> "${ARTIFACTS_DIR}/policy-attestation.md"
        echo "" >> "${ARTIFACTS_DIR}/policy-attestation.md"
    fi
done

cat >> "${ARTIFACTS_DIR}/policy-attestation.md" <<EOF
---
*Generated by GCP Drift Sentinel v0.9.1*
EOF

log_info "Attestation artifacts generated in ${ARTIFACTS_DIR}"

# Exit with appropriate code
if [ ${#ERRORS[@]} -gt 0 ]; then
    echo ""
    log_error "Validation failed with ${#ERRORS[@]} error(s)"
    exit 42  # DRIFT exit code
else
    echo ""
    log_pass "All validations passed!"
    exit 0
fi
