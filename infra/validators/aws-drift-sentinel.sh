#!/bin/bash
set -e

# AWS Drift Sentinel Validator
# Validates AWS guardrails for Codex Controls Matrix v0.9.1

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

# Ensure AWS CLI is available
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install it."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials not configured or invalid."
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

log_info "Running AWS Drift Sentinel"
log_info "Account: ${AWS_ACCOUNT_ID}"
log_info "Region: ${AWS_REGION}"
log_info "Timestamp: ${TIMESTAMP}"
echo ""

# Create artifacts directory
mkdir -p "${ARTIFACTS_DIR}"

# Initialize JSON attestation
cat > "${ARTIFACTS_DIR}/aws-guardrails-attestation.json" <<EOF
{
  "version": "0.9.1",
  "timestamp": "${TIMESTAMP}",
  "account_id": "${AWS_ACCOUNT_ID}",
  "region": "${AWS_REGION}",
  "controls": []
}
EOF

# A1: No Long-Term Credentials (OIDC Role Check)
log_info "Checking A1: No Long-Term Credentials..."
OIDC_ROLE_ARN=${AWS_ROLE_ARN:-""}
if [ -z "$OIDC_ROLE_ARN" ]; then
    log_warning "AWS_ROLE_ARN not set; skipping OIDC role validation"
else
    # Check if role has AdministratorAccess
    ROLE_NAME=$(echo "$OIDC_ROLE_ARN" | awk -F/ '{print $NF}')
    if aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query 'AttachedPolicies[?PolicyName==`AdministratorAccess`]' --output text | grep -q "AdministratorAccess"; then
        log_error "AWS_OIDC_ROLE_LP: OIDC role ${ROLE_NAME} has AdministratorAccess policy attached"
    else
        log_pass "AWS_OIDC_ROLE_LP: OIDC role ${ROLE_NAME} does not have AdministratorAccess"
    fi
fi

# A2: Storage - Public Access Blocked
log_info "Checking A2: Storage Public Access Blocked..."
# Check account-level Public Access Block
if aws s3control get-public-access-block --account-id "$AWS_ACCOUNT_ID" &> /dev/null; then
    PAB_CONFIG=$(aws s3control get-public-access-block --account-id "$AWS_ACCOUNT_ID" --query 'PublicAccessBlockConfiguration' --output json)
    BLOCK_PUBLIC_ACLS=$(echo "$PAB_CONFIG" | jq -r '.BlockPublicAcls')
    IGNORE_PUBLIC_ACLS=$(echo "$PAB_CONFIG" | jq -r '.IgnorePublicAcls')
    BLOCK_PUBLIC_POLICY=$(echo "$PAB_CONFIG" | jq -r '.BlockPublicPolicy')
    RESTRICT_PUBLIC_BUCKETS=$(echo "$PAB_CONFIG" | jq -r '.RestrictPublicBuckets')
    
    if [ "$BLOCK_PUBLIC_ACLS" = "true" ] && [ "$IGNORE_PUBLIC_ACLS" = "true" ] && \
       [ "$BLOCK_PUBLIC_POLICY" = "true" ] && [ "$RESTRICT_PUBLIC_BUCKETS" = "true" ]; then
        log_pass "AWS_S3_ACCOUNT_PAB: Account-level Public Access Block is fully enabled"
    else
        log_error "AWS_S3_ACCOUNT_PAB: Account-level Public Access Block is not fully enabled"
    fi
else
    log_error "AWS_S3_ACCOUNT_PAB: Account-level Public Access Block not configured"
fi

# Check bucket-level posture
NONCOMPLIANT_BUCKETS=0
BUCKETS=$(aws s3api list-buckets --query 'Buckets[].Name' --output text)
for bucket in $BUCKETS; do
    # Check bucket PAB
    if ! aws s3api get-public-access-block --bucket "$bucket" &> /dev/null; then
        log_warning "Bucket ${bucket} does not have Public Access Block configured"
        ((NONCOMPLIANT_BUCKETS++))
        continue
    fi
    
    BUCKET_PAB=$(aws s3api get-public-access-block --bucket "$bucket" --query 'PublicAccessBlockConfiguration' --output json 2>/dev/null || echo '{}')
    B_BLOCK_PUBLIC_ACLS=$(echo "$BUCKET_PAB" | jq -r '.BlockPublicAcls // false')
    B_IGNORE_PUBLIC_ACLS=$(echo "$BUCKET_PAB" | jq -r '.IgnorePublicAcls // false')
    B_BLOCK_PUBLIC_POLICY=$(echo "$BUCKET_PAB" | jq -r '.BlockPublicPolicy // false')
    B_RESTRICT_PUBLIC_BUCKETS=$(echo "$BUCKET_PAB" | jq -r '.RestrictPublicBuckets // false')
    
    if [ "$B_BLOCK_PUBLIC_ACLS" != "true" ] || [ "$B_IGNORE_PUBLIC_ACLS" != "true" ] || \
       [ "$B_BLOCK_PUBLIC_POLICY" != "true" ] || [ "$B_RESTRICT_PUBLIC_BUCKETS" != "true" ]; then
        log_warning "Bucket ${bucket} PAB not fully enabled"
        ((NONCOMPLIANT_BUCKETS++))
    fi
    
    # Check for SecureTransport in bucket policy
    BUCKET_POLICY=$(aws s3api get-bucket-policy --bucket "$bucket" --output json 2>/dev/null || echo "{}")
    if [ "$BUCKET_POLICY" != "{}" ]; then
        POLICY_DOC=$(echo "$BUCKET_POLICY" | jq -r '.Policy // "{}"')
        if ! echo "$POLICY_DOC" | jq -e '.Statement[]? | select(.Condition.Bool."aws:SecureTransport" == "false") | select(.Effect == "Deny")' &> /dev/null; then
            log_info "Bucket ${bucket} may not enforce SecureTransport"
        fi
    fi
done

if [ $NONCOMPLIANT_BUCKETS -eq 0 ]; then
    log_pass "AWS_S3_BUCKET_POSTURE: All buckets have proper Public Access Block configuration"
else
    log_error "AWS_S3_BUCKET_POSTURE: ${NONCOMPLIANT_BUCKETS} bucket(s) are non-compliant"
fi

# A6: Audit Logging - CloudTrail
log_info "Checking A6: CloudTrail Multi-Region Logging..."
TRAILS=$(aws cloudtrail describe-trails --query 'trailList' --output json)
MULTI_REGION_TRAIL_FOUND=false

if [ "$(echo "$TRAILS" | jq '. | length')" -eq 0 ]; then
    log_error "AWS_CLOUDTRAIL_LOGGING: No CloudTrail trails found"
else
    while IFS= read -r trail; do
        TRAIL_NAME=$(echo "$trail" | jq -r '.Name')
        IS_MULTI_REGION=$(echo "$trail" | jq -r '.IsMultiRegionTrail')
        IS_LOGGING=$(aws cloudtrail get-trail-status --name "$TRAIL_NAME" --query 'IsLogging' --output text 2>/dev/null || echo "false")
        
        if [ "$IS_MULTI_REGION" = "true" ] && [ "$IS_LOGGING" = "True" ]; then
            MULTI_REGION_TRAIL_FOUND=true
            log_pass "AWS_CLOUDTRAIL_LOGGING: Trail ${TRAIL_NAME} is multi-region and logging"
            break
        fi
    done < <(echo "$TRAILS" | jq -c '.[]')
    
    if [ "$MULTI_REGION_TRAIL_FOUND" = false ]; then
        log_error "AWS_CLOUDTRAIL_LOGGING: No active multi-region CloudTrail trail found"
    fi
fi

# A7: KMS Key Rotation
log_info "Checking A7: KMS Key Rotation..."
KMS_KEYS=$(aws kms list-keys --query 'Keys[].KeyId' --output text)
NONCOMPLIANT_KEYS=0

for key_id in $KMS_KEYS; do
    KEY_METADATA=$(aws kms describe-key --key-id "$key_id" --query 'KeyMetadata' --output json)
    KEY_MANAGER=$(echo "$KEY_METADATA" | jq -r '.KeyManager')
    KEY_STATE=$(echo "$KEY_METADATA" | jq -r '.KeyState')
    
    # Only check customer-managed keys that are enabled
    if [ "$KEY_MANAGER" = "CUSTOMER" ] && [ "$KEY_STATE" = "Enabled" ]; then
        ROTATION_ENABLED=$(aws kms get-key-rotation-status --key-id "$key_id" --query 'KeyRotationEnabled' --output text 2>/dev/null || echo "False")
        
        if [ "$ROTATION_ENABLED" != "True" ]; then
            log_warning "KMS key ${key_id} does not have rotation enabled"
            ((NONCOMPLIANT_KEYS++))
        fi
    fi
done

if [ $NONCOMPLIANT_KEYS -eq 0 ]; then
    log_pass "AWS_KMS_ROTATION: All customer-managed KMS keys have rotation enabled"
else
    log_error "AWS_KMS_ROTATION: ${NONCOMPLIANT_KEYS} key(s) do not have rotation enabled"
fi

# Generate summary
echo ""
log_info "=== Validation Summary ==="
echo "Passed: ${#PASSED[@]}"
echo "Warnings: ${#WARNINGS[@]}"
echo "Errors: ${#ERRORS[@]}"

# Generate attestation JSON
cat > "${ARTIFACTS_DIR}/aws-guardrails-attestation.json" <<EOF
{
  "version": "0.9.1",
  "timestamp": "${TIMESTAMP}",
  "account_id": "${AWS_ACCOUNT_ID}",
  "region": "${AWS_REGION}",
  "controls": [
    {
      "id": "A1",
      "name": "No Long-Term Credentials",
      "status": "$([ ${#ERRORS[@]} -eq 0 ] && echo "compliant" || echo "non-compliant")",
      "checks": {
        "oidc_role": "$([ -z "$OIDC_ROLE_ARN" ] && echo "skipped" || echo "checked")"
      }
    },
    {
      "id": "A2",
      "name": "Storage Public Access Blocked",
      "status": "$([ $NONCOMPLIANT_BUCKETS -eq 0 ] && echo "compliant" || echo "non-compliant")",
      "noncompliant_buckets": $NONCOMPLIANT_BUCKETS
    },
    {
      "id": "A6",
      "name": "CloudTrail Multi-Region Logging",
      "status": "$([ "$MULTI_REGION_TRAIL_FOUND" = true ] && echo "compliant" || echo "non-compliant")"
    },
    {
      "id": "A7",
      "name": "KMS Key Rotation",
      "status": "$([ $NONCOMPLIANT_KEYS -eq 0 ] && echo "compliant" || echo "non-compliant")",
      "noncompliant_keys": $NONCOMPLIANT_KEYS
    }
  ],
  "summary": {
    "passed": ${#PASSED[@]},
    "warnings": ${#WARNINGS[@]},
    "errors": ${#ERRORS[@]}
  }
}
EOF

# Generate SARIF
cat > "${ARTIFACTS_DIR}/aws-guardrails-attestation.sarif" <<EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "AWS Drift Sentinel",
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
cat > "${ARTIFACTS_DIR}/aws-guardrails-attestation.md" <<EOF
# AWS Guardrails Attestation Report

**Version:** 0.9.1  
**Timestamp:** ${TIMESTAMP}  
**Account:** ${AWS_ACCOUNT_ID}  
**Region:** ${AWS_REGION}

## Summary

- ✅ Passed: ${#PASSED[@]}
- ⚠️  Warnings: ${#WARNINGS[@]}
- ❌ Errors: ${#ERRORS[@]}

## Control Results

### A1: No Long-Term Credentials
Status: $([ ${#ERRORS[@]} -eq 0 ] && echo "✅ Compliant" || echo "❌ Non-Compliant")

### A2: Storage Public Access Blocked
Status: $([ $NONCOMPLIANT_BUCKETS -eq 0 ] && echo "✅ Compliant" || echo "⚠️ Non-Compliant")
- Non-compliant buckets: ${NONCOMPLIANT_BUCKETS}

### A6: CloudTrail Multi-Region Logging
Status: $([ "$MULTI_REGION_TRAIL_FOUND" = true ] && echo "✅ Compliant" || echo "❌ Non-Compliant")

### A7: KMS Key Rotation
Status: $([ $NONCOMPLIANT_KEYS -eq 0 ] && echo "✅ Compliant" || echo "⚠️ Non-Compliant")
- Non-compliant keys: ${NONCOMPLIANT_KEYS}

---
*Generated by AWS Drift Sentinel v0.9.1*
EOF

# Generate CSV
cat > "${ARTIFACTS_DIR}/aws-guardrails-attestation.csv" <<EOF
Control ID,Control Name,Status,Details
A1,No Long-Term Credentials,$([ ${#ERRORS[@]} -eq 0 ] && echo "compliant" || echo "non-compliant"),OIDC role checked
A2,Storage Public Access Blocked,$([ $NONCOMPLIANT_BUCKETS -eq 0 ] && echo "compliant" || echo "non-compliant"),${NONCOMPLIANT_BUCKETS} buckets non-compliant
A6,CloudTrail Multi-Region Logging,$([ "$MULTI_REGION_TRAIL_FOUND" = true ] && echo "compliant" || echo "non-compliant"),Multi-region trail status
A7,KMS Key Rotation,$([ $NONCOMPLIANT_KEYS -eq 0 ] && echo "compliant" || echo "non-compliant"),${NONCOMPLIANT_KEYS} keys non-compliant
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
