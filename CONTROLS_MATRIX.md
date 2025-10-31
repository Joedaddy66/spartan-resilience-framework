# Controls Matrix — Codex Guardrails v0.9.1 (Rosetta)

*A single pane of glass mapping Codex doctrine → cloud-specific controls → CI evidence.*

**Version:** v0.9.1  
**Scope:** Azure · AWS · GCP  
**Evidence Artifacts:** JSON · SARIF · MD · CSV · XLSX

---

## Legend

* **Status:** ✅ Enforced in 0.9.1 · 🟡 Partial (enforced for subset) · 🔭 Planned (v1.0) · ⭕ N/A
* **Evidence:** Attestation files emitted by drift-sentinel validators
* **IDs:** Use repo variables / Terraform outputs where noted

---

## A. Control Coverage Matrix

|  # | Control (Objective)                                                                 | **Azure**                                                                                                            | **AWS**                                                                                                                                               | **GCP**                                                                                                                                                                                                                   | Status |
| -: | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| A1 | **No long-term credentials** (OIDC-only pipelines; block access key minting/upload) | RBAC sanity: OIDC SP not `Owner` at sub scope (validator rule `AZ_RBAC`); **Policy** (CI): OIDC via `azure/login@v2` | **SCP**: `scp/deny-long-term-creds.json` (deny IAM user keys); OIDC via `aws-actions/configure-aws-credentials@v4`; validator rule `AWS_OIDC_ROLE_LP` | **Org Policy** profile (**Terraform**): `constraints/iam.disableServiceAccountKeyCreation` + `iam.managed.disableServiceAccountKeyUpload` + `iam.managed.disableServiceAccountApiKeyCreation`; WIF/OIDC federation for CI | ✅      |
| A2 | **Storage: Public access blocked (or PrivateLink)**                                 | **Policy/Resource posture:** `publicNetworkAccess=Disabled` **or** Private Endpoint; validator `AZ_RES_STG_POSTURE`  | **Account PAB** + bucket PAB + `aws:SecureTransport` check in policy; validator `AWS_S3_ACCOUNT_PAB` + `AWS_S3_BUCKET_POSTURE`                        | **Org Policy:** `constraints/storage.publicAccessPrevention=Enforced`; bucket `iamConfiguration.uniformBucketLevelAccess=true`                                                                                            | ✅      |
| A3 | **Storage: Disable legacy/shared key auth**                                         | `allowSharedKeyAccess=false` (validator enforces)                                                                    | ⭕ (Not directly analogous in S3; access uses SigV4/Access Keys. Enforce via IAM/SCP; covered in A1)                                                   | ⭕                                                                                                                                                                                                                         | 🟡     |
| A4 | **Transport security: Minimum TLS**                                                 | `minimumTlsVersion>=TLS1_2` on Storage (validator)                                                                   | `aws:SecureTransport` enforced in S3 bucket policy (HTTPS required)                                                                                   | ⭕ (GCS uses HTTPS by default; per-resource TLS min not configurable)                                                                                                                                                      | ✅      |
| A5 | **Key Vault / Secrets: No public exposure + Purge Protection**                      | `publicNetworkAccess=Disabled` or Private Endpoint **and** `enablePurgeProtection=true` (validator)                  | 🔭 (Map to KMS key deletion protection / SSM Parameter Store policies; not in current validator)                                                      | 🔭 (Secret Manager access is IAM/VPC-SC; no purge protection equivalent)                                                                                                                                                  | 🟡     |
| A6 | **Audit Logging** (Provider-level audit on)                                         | 🔭 (Activity Log export/diagnostics policy & sentinel)                                                               | **CloudTrail** multi-region logging enforced (validator rule `AWS_CLOUDTRAIL_LOGGING`)                                                                | 🔭 (Cloud Audit Logs org sink; policy check)                                                                                                                                                                              | 🟡     |
| A7 | **Key Management: Rotation enabled**                                                | 🔭 (Key Vault rotation policy check)                                                                                 | **KMS** rotation required (validator `AWS_KMS_ROTATION`)                                                                                              | 🔭 (Cloud KMS key rotation schedule)                                                                                                                                                                                      | 🟡     |
| A8 | **RBAC/Least Privilege** (service principals/roles)                                 | OIDC SP not `Owner` (error) / `Contributor` (warn) at subscription (validator)                                       | OIDC role must not have `AdministratorAccess` (validator)                                                                                             | Profile blocks privileged roles on default SAs; Terraform bindings minimal                                                                                                                                                | ✅      |

> *Note:* Azure *Storage* posture in A2 includes a fallback: if `publicNetworkAccess` is not `Disabled`, a **Private Endpoint** must exist. The validator treats either path as compliant.

---

## B. Policy / ID Mapping

### Azure (variables → built-in policy definitions)

* **Storage – No Shared Key** → `${{ vars.AZ_POLICY_STG_NO_SHARED_ID }}`
* **Key Vault – No Public** → `${{ vars.AZ_POLICY_KV_NO_PUBLIC_ID }}`
* *(Optional)* **Key Vault – Purge Protection** → `${{ vars.AZ_POLICY_KV_PURGE_ID }}`
* *(Optional)* **Storage – Minimum TLS** → `${{ vars.AZ_POLICY_STG_TLS_ID }}`

**Evidence (files)**

* `infra/artifacts/azure-policy-attestation.json|.sarif|.md`
* `infra/artifacts/azure-noncompliant.csv`
* `infra/artifacts/azure-private-link-coverage.csv`
* `infra/artifacts/azure-attestation.xlsx`

**Workflow**

* `.github/workflows/azure-drift-sentinel.yml`

---

### AWS (SCPs / role / region)

* **Repo Secrets/Vars:** `AWS_ROLE_ARN` · `AWS_REGION` · `AWS_ACCOUNT_ID`
* **SCPs:**

  * `scp/deny-long-term-creds.json` (deny IAM user management & access keys)
  * `scp/deny-s3-public.json` (block S3 public policies & ACLs)
  * `scp/deny-cloudtrail-stop.json` (prevent disabling/deleting trails)
* **OIDC Role (Terraform module):** `modules/github-oidc-aws` → output `role_arn`

**Evidence (files)**

* `infra/artifacts/aws-guardrails-attestation.json|.sarif|.md|.csv`
* `infra/artifacts/aws-attestation.xlsx`

**Workflow**

* `.github/workflows/aws-drift-sentinel.yml`

---

### GCP (Org Policies / WIF)

* **Profile Variable:** `harden_service_accounts_profile` = `STRICT|DEFAULT|CUSTOM`
* **Key org policies (via module variables):**

  * `constraints/iam.disableServiceAccountKeyCreation`
  * `constraints/iam.disableServiceAccountKeyUpload` (note: newer GCP constraint naming)
  * *(Note: API key creation restrictions handled via IAM policies)*
  * *(Optional)* Leaf-project SA creation off; default SA privilege guards
* **WIF/OIDC:** Workload Identity Federation → GitHub OIDC pool + binding to runtime SA

**Evidence (files & scripts)**

* *(If present)* `infra/artifacts/gcp-org-policy-attestation.json|.sarif`
* Terraform apply output + `policy-attestation.md`
* Post-apply validator: `infra/validators/gcp-drift-sentinel.sh` (project/org scope)

**Workflow**

* *(If present)* `.github/workflows/gcp-drift-sentinel.yml`

---

## C. CI Evidence & Acceptance

| Control                   | Azure Evidence                               | AWS Evidence                                                     | GCP Evidence                                       | Acceptance Criteria (CI)                        |
| ------------------------- | -------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------- |
| A1 No long-term creds     | `AZ_RBAC` errors=0                           | `AWS_OIDC_ROLE_LP` level≠error                                   | Org policies all `enforced`                        | Sentinel exit 0; PR gate green                  |
| A2 Storage public blocked | `AZ_RES_STG_POSTURE` noncompliant=0          | `AWS_S3_ACCOUNT_PAB` ok & `AWS_S3_BUCKET_POSTURE` noncompliant=0 | `storage.publicAccessPrevention=Enforced`; UBLE=On | Sentinel exit 0                                 |
| A3 Disable shared key     | `allowSharedKeyAccess=false` across accounts | ⭕                                                                | ⭕                                                  | Azure noncompliant=0                            |
| A4 TLS minimum            | `minimumTlsVersion>=TLS1_2`                  | `SecureTransport` required                                       | ⭕                                                  | Azure noncompliant=0; AWS bucket noncompliant=0 |
| A5 KV purge protect       | `enablePurgeProtection=true`                 | 🔭                                                               | 🔭                                                 | Azure noncompliant=0 (if enabled)               |
| A6 Audit logging          | 🔭                                           | CloudTrail multi-region logging=on                               | 🔭                                                 | AWS control status=ok                           |
| A7 KMS rotation           | 🔭                                           | KeyRotationEnabled for all KMS keys                              | 🔭                                                 | AWS noncompliant=0                              |
| A8 RBAC least privilege   | OIDC SP not Owner (error), Contrib (warn)    | OIDC role not AdminAccess                                        | Default SA privilege blocks                        | No errors, warnings acceptable per policy       |

---

## D. CLI Verification (spot checks)

**Azure**

```bash
# Assignment present & enforced
az policy assignment list --disable-scope-strict-match -o table | grep -E "(KV|Storage)"
# Storage posture (sample)
az storage account list -o json | jq -r '.[] | {name, allowSharedKeyAccess: .properties.allowSharedKeyAccess, publicNetworkAccess: .properties.publicNetworkAccess, minTLS: .properties.minimumTlsVersion}'
# Key Vault posture (sample)
az keyvault list -o json | jq -r '.[] | {name, publicNetworkAccess: .properties.publicNetworkAccess, purge: .properties.enablePurgeProtection, pe: (.properties.privateEndpointConnections|length)}'
```

**AWS**

```bash
# Account PAB
aws s3control get-public-access-block --account-id $AWS_ACCOUNT_ID | jq
# Buckets posture (sample)
for b in $(aws s3api list-buckets | jq -r '.Buckets[].Name'); do
  aws s3api get-public-access-block --bucket "$b" 2>/dev/null | jq -r '.PublicAccessBlockConfiguration';
  aws s3api get-bucket-policy --bucket "$b" 2>/dev/null | jq -r '.Policy' | jq -r 'try fromjson catch empty' | grep -A2 SecureTransport || true;
done
# CloudTrail logging
aws cloudtrail describe-trails --include-shadow-trails | jq -r '.trailList[] | {name: .Name, multiRegion: .IsMultiRegionTrail}'
```

**GCP**

```bash
# Org policies (examples)
gcloud org-policies describe constraints/iam.disableServiceAccountKeyCreation --organization <ORG_ID>
gcloud org-policies describe constraints/storage.publicAccessPrevention --organization <ORG_ID>
# WIF bindings (sample)
gcloud iam workload-identity-pools providers describe github --location=global --workload-identity-pool=<POOL>
```

---

## E. Severity & Ownership

| Control                       | Severity | Default Owner         | Escalation   |
| ----------------------------- | -------: | --------------------- | ------------ |
| A1 No long-term creds         | Critical | Platform Security     | Security CAB |
| A2 Storage public blocked     |     High | Cloud Ops (per cloud) | Security CAB |
| A3 Disable shared key (Azure) |     High | Azure Platform        | Security CAB |
| A4 TLS minimum                |     High | Cloud Ops             | Security CAB |
| A5 KV purge protect           |     High | Azure Platform        | Security CAB |
| A6 Audit logging              |     High | Cloud SecOps          | Security CAB |
| A7 KMS rotation               |   Medium | Cloud SecOps          | Security CAB |
| A8 RBAC least privilege       |     High | IAM / Platform        | Security CAB |

---

## F. How this reads on the artifacts

* **Azure**: `azure-policy-attestation.json` → `policy_controls[]`, `resource_controls[]`, `rbac.findings[]`
* **AWS**: `aws-guardrails-attestation.json` → `controls[]`
* **GCP**: `policy-attestation.md` + *(optional)* `gcp-org-policy-attestation.json`

> CI gates: Sentinel exit code `0`=PASS, `42`=DRIFT. Code Scanning shows SARIF categories: `azure-policy-drift`, `aws-policy-drift`.

---

## G. Roadmap to v1.0.0 (additions to matrix)

* Azure: **Key Vault rotation policy** enforcement; Activity Log diagnostics policies + sentinel checks
* AWS: **Config** conformance packs mapping for S3/KMS/CloudTrail; VPC Endpoint checks for critical services
* GCP: **Audit log sinks** org coverage; **VPC-SC** posture snapshot; per-bucket PAP/UBLA sweeps
* Cross-cloud: **Controls Matrix → SARIF mapping** with remediation URLs; **CSV/XLSX** enriched with owner/severity

---

## Implementation Guide

### Getting Started

1. **Set up cloud credentials**: Configure OIDC authentication for each cloud provider in your GitHub repository settings.

2. **Configure repository secrets and variables**:

   **Azure:**
   - Secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
   - Variables (optional): `AZ_POLICY_STG_NO_SHARED_ID`, `AZ_POLICY_KV_NO_PUBLIC_ID`, etc.

   **AWS:**
   - Secrets: `AWS_ROLE_ARN`, `AWS_ACCOUNT_ID`
   - Variables: `AWS_REGION` (default: us-east-1)

   **GCP:**
   - Secrets: `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`
   - Variables: `GCP_PROJECT_ID`, `GCP_ORG_ID` (for org-level policies)

3. **Deploy infrastructure**:

   **AWS OIDC Role:**
   ```bash
   cd infra
   terraform init
   terraform apply -target=module.github_oidc_aws
   ```

   **GCP Org Policies:**
   ```bash
   cd infra
   terraform init
   terraform apply -target=module.gcp_org_policies
   ```

   **Offline/Firewall-Safe Terraform Validation:**
   
   If operating in an egress-restricted environment, use the reusable composite action:
   
   ```yaml
   - uses: ./.github/actions/tf-offline-validate
     with:
       terraform_version: '1.9.5'
       working_directory: 'infra'
       gcp_workload_identity_provider: ${{ secrets.GCP_WIF_PROVIDER }}
       gcp_service_account: ${{ secrets.GCP_WIF_SA }}
   ```
   
   This action:
   - Pre-warms provider cache before firewall enforcement
   - Disables Terraform checkpoint calls (`CHECKPOINT_DISABLE=1`)
   - Authenticates to cloud providers to avoid metadata probes
   - Validates configuration offline using cached providers
   
   See `.github/actions/tf-offline-validate/README.md` for details and local CLI equivalents.

4. **Enable workflows**: The drift-sentinel workflows will run automatically on schedule or can be triggered manually.

### Manual Validation

You can run the validators locally:

```bash
# AWS
AWS_ROLE_ARN=<your-role-arn> AWS_REGION=us-east-1 AWS_ACCOUNT_ID=<id> \
  bash infra/validators/aws-drift-sentinel.sh

# Azure (requires az login)
bash infra/validators/azure-drift-sentinel.sh

# GCP (requires gcloud auth)
GCP_PROJECT_ID=<project> GCP_ORG_ID=<org-id> \
  bash infra/validators/gcp-drift-sentinel.sh
```

### Interpreting Results

- **Exit code 0**: All controls are compliant
- **Exit code 42**: Drift detected (policy violations)
- **Artifacts**: Check `infra/artifacts/` for detailed reports in JSON, SARIF, MD, and CSV formats

---

*End of matrix.*
