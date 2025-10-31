#!/bin/bash
set -e

# Azure Drift Sentinel Validator
# Validates Azure guardrails for Codex Controls Matrix v0.9.1

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

# Ensure Azure CLI is available
if ! command -v az &> /dev/null; then
    log_error "Azure CLI not found. Please install it."
    exit 1
fi

# Check Azure login
if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Run 'az login' first."
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)

log_info "Running Azure Drift Sentinel"
log_info "Subscription: ${SUBSCRIPTION_NAME} (${SUBSCRIPTION_ID})"
log_info "Timestamp: ${TIMESTAMP}"
echo ""

# Create artifacts directory
mkdir -p "${ARTIFACTS_DIR}"

# Initialize tracking arrays
declare -a POLICY_CONTROLS=()
declare -a RESOURCE_CONTROLS=()
declare -a RBAC_FINDINGS=()

# A8: RBAC - Check OIDC Service Principal permissions
log_info "Checking A8: RBAC Least Privilege..."
# Get current service principal if using OIDC
SP_OBJECT_ID=$(az account show --query user.name -o tsv 2>/dev/null || echo "")

if [ -n "$SP_OBJECT_ID" ]; then
    # Check subscription-level role assignments
    ROLE_ASSIGNMENTS=$(az role assignment list --assignee "$SP_OBJECT_ID" --scope "/subscriptions/${SUBSCRIPTION_ID}" --query '[].{role:roleDefinitionName}' -o json)
    
    if echo "$ROLE_ASSIGNMENTS" | jq -e '.[] | select(.role == "Owner")' &> /dev/null; then
        log_error "AZ_RBAC: Service Principal has Owner role at subscription scope"
        RBAC_FINDINGS+=('{"level":"error","message":"Service Principal has Owner role at subscription scope"}')
    elif echo "$ROLE_ASSIGNMENTS" | jq -e '.[] | select(.role == "Contributor")' &> /dev/null; then
        log_warning "AZ_RBAC: Service Principal has Contributor role at subscription scope (consider least privilege)"
        RBAC_FINDINGS+=('{"level":"warning","message":"Service Principal has Contributor role at subscription scope"}')
    else
        log_pass "AZ_RBAC: Service Principal does not have Owner or Contributor at subscription scope"
        RBAC_FINDINGS+=('{"level":"pass","message":"Service Principal follows least privilege"}')
    fi
else
    log_info "AZ_RBAC: Not running as service principal, skipping RBAC check"
fi

# A2: Storage - Public Network Access
log_info "Checking A2: Storage Account Public Access..."
STORAGE_ACCOUNTS=$(az storage account list --query '[].{name:name,rg:resourceGroup}' -o json)
NONCOMPLIANT_STORAGE=0

while IFS= read -r account; do
    ACCOUNT_NAME=$(echo "$account" | jq -r '.name')
    ACCOUNT_RG=$(echo "$account" | jq -r '.rg')
    
    ACCOUNT_DETAILS=$(az storage account show -n "$ACCOUNT_NAME" -g "$ACCOUNT_RG" -o json)
    PUBLIC_NETWORK_ACCESS=$(echo "$ACCOUNT_DETAILS" | jq -r '.publicNetworkAccess // "Enabled"')
    ALLOW_SHARED_KEY=$(echo "$ACCOUNT_DETAILS" | jq -r '.allowSharedKeyAccess // true')
    MIN_TLS=$(echo "$ACCOUNT_DETAILS" | jq -r '.minimumTlsVersion // "TLS1_0"')
    PRIVATE_ENDPOINTS=$(echo "$ACCOUNT_DETAILS" | jq -r '.privateEndpointConnections | length')
    
    # A2: Check public network access or private endpoint
    if [ "$PUBLIC_NETWORK_ACCESS" != "Disabled" ] && [ "$PRIVATE_ENDPOINTS" -eq 0 ]; then
        log_error "AZ_RES_STG_POSTURE: Storage account ${ACCOUNT_NAME} has public network access and no private endpoints"
        ((NONCOMPLIANT_STORAGE++))
        RESOURCE_CONTROLS+=("{\"account\":\"${ACCOUNT_NAME}\",\"control\":\"A2\",\"status\":\"non-compliant\",\"reason\":\"Public access enabled without private endpoint\"}")
    else
        log_pass "AZ_RES_STG_POSTURE: Storage account ${ACCOUNT_NAME} has proper network posture"
        RESOURCE_CONTROLS+=("{\"account\":\"${ACCOUNT_NAME}\",\"control\":\"A2\",\"status\":\"compliant\"}")
    fi
    
    # A3: Check shared key access
    if [ "$ALLOW_SHARED_KEY" = "true" ]; then
        log_warning "Storage account ${ACCOUNT_NAME} allows shared key access"
        ((NONCOMPLIANT_STORAGE++))
        RESOURCE_CONTROLS+=("{\"account\":\"${ACCOUNT_NAME}\",\"control\":\"A3\",\"status\":\"non-compliant\",\"reason\":\"Shared key access enabled\"}")
    else
        log_pass "Storage account ${ACCOUNT_NAME} has shared key access disabled"
        RESOURCE_CONTROLS+=("{\"account\":\"${ACCOUNT_NAME}\",\"control\":\"A3\",\"status\":\"compliant\"}")
    fi
    
    # A4: Check TLS version
    if [[ "$MIN_TLS" < "TLS1_2" ]]; then
        log_error "Storage account ${ACCOUNT_NAME} has minimum TLS version ${MIN_TLS} (should be TLS1_2 or higher)"
        ((NONCOMPLIANT_STORAGE++))
        RESOURCE_CONTROLS+=("{\"account\":\"${ACCOUNT_NAME}\",\"control\":\"A4\",\"status\":\"non-compliant\",\"reason\":\"TLS version below 1.2\"}")
    else
        log_pass "Storage account ${ACCOUNT_NAME} has minimum TLS ${MIN_TLS}"
        RESOURCE_CONTROLS+=("{\"account\":\"${ACCOUNT_NAME}\",\"control\":\"A4\",\"status\":\"compliant\"}")
    fi
done < <(echo "$STORAGE_ACCOUNTS" | jq -c '.[]')

# A5: Key Vault - Public Network Access and Purge Protection
log_info "Checking A5: Key Vault Security..."
KEY_VAULTS=$(az keyvault list --query '[].{name:name,rg:resourceGroup}' -o json)
NONCOMPLIANT_KV=0

while IFS= read -r vault; do
    VAULT_NAME=$(echo "$vault" | jq -r '.name')
    VAULT_RG=$(echo "$vault" | jq -r '.rg')
    
    VAULT_DETAILS=$(az keyvault show -n "$VAULT_NAME" -g "$VAULT_RG" -o json)
    PUBLIC_NETWORK_ACCESS=$(echo "$VAULT_DETAILS" | jq -r '.properties.publicNetworkAccess // "Enabled"')
    PURGE_PROTECTION=$(echo "$VAULT_DETAILS" | jq -r '.properties.enablePurgeProtection // false')
    PRIVATE_ENDPOINTS=$(echo "$VAULT_DETAILS" | jq -r '.properties.privateEndpointConnections | length')
    
    # Check public network access or private endpoint
    if [ "$PUBLIC_NETWORK_ACCESS" != "Disabled" ] && [ "$PRIVATE_ENDPOINTS" -eq 0 ]; then
        log_error "Key Vault ${VAULT_NAME} has public network access and no private endpoints"
        ((NONCOMPLIANT_KV++))
    else
        log_pass "Key Vault ${VAULT_NAME} has proper network posture"
    fi
    
    # Check purge protection
    if [ "$PURGE_PROTECTION" != "true" ]; then
        log_warning "Key Vault ${VAULT_NAME} does not have purge protection enabled"
        ((NONCOMPLIANT_KV++))
    else
        log_pass "Key Vault ${VAULT_NAME} has purge protection enabled"
    fi
    
    RESOURCE_CONTROLS+=("{\"vault\":\"${VAULT_NAME}\",\"control\":\"A5\",\"publicAccess\":\"${PUBLIC_NETWORK_ACCESS}\",\"purgeProtection\":${PURGE_PROTECTION}}")
done < <(echo "$KEY_VAULTS" | jq -c '.[]')

# Check Policy Assignments (optional based on variables)
log_info "Checking Azure Policy Assignments..."
POLICY_ASSIGNMENTS=$(az policy assignment list --disable-scope-strict-match -o json)

# Common policies to check
declare -A POLICY_CHECKS=(
    ["storage-no-shared-key"]="${AZ_POLICY_STG_NO_SHARED_ID:-}"
    ["keyvault-no-public"]="${AZ_POLICY_KV_NO_PUBLIC_ID:-}"
    ["keyvault-purge-protection"]="${AZ_POLICY_KV_PURGE_ID:-}"
    ["storage-minimum-tls"]="${AZ_POLICY_STG_TLS_ID:-}"
)

for policy_name in "${!POLICY_CHECKS[@]}"; do
    policy_id="${POLICY_CHECKS[$policy_name]}"
    if [ -n "$policy_id" ]; then
        if echo "$POLICY_ASSIGNMENTS" | jq -e ".[] | select(.properties.policyDefinitionId | contains(\"${policy_id}\"))" &> /dev/null; then
            log_pass "Policy ${policy_name} is assigned"
            POLICY_CONTROLS+=("{\"name\":\"${policy_name}\",\"status\":\"assigned\"}")
        else
            log_warning "Policy ${policy_name} (${policy_id}) is not assigned"
            POLICY_CONTROLS+=("{\"name\":\"${policy_name}\",\"status\":\"not-assigned\"}")
        fi
    fi
done

# Generate summary
echo ""
log_info "=== Validation Summary ==="
echo "Passed: ${#PASSED[@]}"
echo "Warnings: ${#WARNINGS[@]}"
echo "Errors: ${#ERRORS[@]}"
echo "Non-compliant storage accounts: ${NONCOMPLIANT_STORAGE}"
echo "Non-compliant key vaults: ${NONCOMPLIANT_KV}"

# Generate JSON attestation
cat > "${ARTIFACTS_DIR}/azure-policy-attestation.json" <<EOF
{
  "version": "0.9.1",
  "timestamp": "${TIMESTAMP}",
  "subscription_id": "${SUBSCRIPTION_ID}",
  "subscription_name": "${SUBSCRIPTION_NAME}",
  "policy_controls": [$(IFS=,; echo "${POLICY_CONTROLS[*]}")],
  "resource_controls": [$(IFS=,; echo "${RESOURCE_CONTROLS[*]}")],
  "rbac": {
    "findings": [$(IFS=,; echo "${RBAC_FINDINGS[*]}")]
  },
  "summary": {
    "passed": ${#PASSED[@]},
    "warnings": ${#WARNINGS[@]},
    "errors": ${#ERRORS[@]},
    "noncompliant_storage": ${NONCOMPLIANT_STORAGE},
    "noncompliant_keyvaults": ${NONCOMPLIANT_KV}
  }
}
EOF

# Generate SARIF
cat > "${ARTIFACTS_DIR}/azure-policy-attestation.sarif" <<EOF
{
  "\$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Azure Drift Sentinel",
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
cat > "${ARTIFACTS_DIR}/azure-policy-attestation.md" <<EOF
# Azure Policy Attestation Report

**Version:** 0.9.1  
**Timestamp:** ${TIMESTAMP}  
**Subscription:** ${SUBSCRIPTION_NAME}  
**Subscription ID:** ${SUBSCRIPTION_ID}

## Summary

- ✅ Passed: ${#PASSED[@]}
- ⚠️  Warnings: ${#WARNINGS[@]}
- ❌ Errors: ${#ERRORS[@]}

## Resource Compliance

### Storage Accounts
- Non-compliant: ${NONCOMPLIANT_STORAGE}

### Key Vaults
- Non-compliant: ${NONCOMPLIANT_KV}

## Control Results

### A2: Storage Public Access Blocked
Status: $([ $NONCOMPLIANT_STORAGE -eq 0 ] && echo "✅ Compliant" || echo "⚠️ Non-Compliant")

### A3: Storage Shared Key Access Disabled
Status: $([ $NONCOMPLIANT_STORAGE -eq 0 ] && echo "✅ Compliant" || echo "⚠️ Non-Compliant")

### A4: Storage Minimum TLS
Status: $([ $NONCOMPLIANT_STORAGE -eq 0 ] && echo "✅ Compliant" || echo "⚠️ Non-Compliant")

### A5: Key Vault Security
Status: $([ $NONCOMPLIANT_KV -eq 0 ] && echo "✅ Compliant" || echo "⚠️ Non-Compliant")

### A8: RBAC Least Privilege
Status: $([ ${#ERRORS[@]} -eq 0 ] && echo "✅ Compliant" || echo "❌ Non-Compliant")

---
*Generated by Azure Drift Sentinel v0.9.1*
EOF

# Generate CSV reports
cat > "${ARTIFACTS_DIR}/azure-noncompliant.csv" <<EOF
Resource Type,Resource Name,Control,Status,Reason
EOF

# Add non-compliant resources to CSV
for control in "${RESOURCE_CONTROLS[@]}"; do
    echo "$control" | jq -r 'select(.status == "non-compliant") | [.account // .vault, .control, .status, .reason // ""] | @csv' >> "${ARTIFACTS_DIR}/azure-noncompliant.csv"
done

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
