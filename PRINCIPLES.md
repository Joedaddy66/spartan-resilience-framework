# Spartan Resilience Framework: Core Principles

This document outlines the fundamental design principles of the Spartan Resilience Framework. While the Apache 2.0 license governs the legal use of the software, these principles represent the technical and ethical commitments of the project.

The purpose of the Spartan Resilience Framework is to create a verifiable, high-integrity system for AI-human coexistence governance with integrated FinOps, telemetry, and policy enforcement that produces auditable, tamper-evident records for digital artifacts and operational decisions.

## 1. Immutable Audit Trail

**Principle:** All verification actions, policy decisions, and administrative overrides must be recorded in an append-only log.

**Technical Enforcement:** The system is designed to log all signature and verification events to a persistent, tamper-evident ledger. This logging mechanism is a core function and cannot be disabled through standard configuration. All event logs are HMAC-signed using a secret key (`SAVE_HMAC_SECRET`) to ensure authenticity and detect tampering.

## 2. Cryptographic Integrity of Core Functions

**Principle:** The software's core hashing and cryptographic signing functions are critical to its purpose. A modified or compromised version cannot provide the same level of trust.

**Technical Enforcement:** The system implements cryptographic safeguards for audit trails and policy enforcement. Security scanning is integrated into the CI/CD pipeline, including dependency vulnerability checks with Safety, static analysis with Bandit, and automated SBOM generation for supply chain security. The system's integrity depends on these cryptographic primitives remaining uncompromised.

## 3. Purpose-Bound Use

**Principle:** This software is an instrument for creating truth and transparency in AI governance and operations. Using it to generate misleading or fraudulent attestations is a misuse contrary to its design.

**Technical Enforcement:** While the software cannot know user intent, the signed event logs bind resource metrics, cost data, policy decisions, and governance context together, making fraudulent claims difficult to construct and easy to disprove. The fail-closed policy enforcement ensures that operations without proper authorization or compliance are denied by default.

## 4. Verifiable by Default

**Principle:** A record of verification or policy enforcement is only useful if its authenticity can be independently checked.

**Technical Enforcement:** The system uses standard, well-vetted cryptographic libraries (HMAC-SHA256 for event signing, industry-standard hashing algorithms) for signatures and verification. Policy decisions are backed by Open Policy Agent (OPA) with Rego policies that can be independently validated. All telemetry metrics, cost calculations, and compliance decisions are logged with cryptographic signatures, enabling independent verification of system behavior.

## 5. Fail-Closed Security

**Principle:** Security and compliance controls must fail in a safe state. When in doubt, the system denies rather than permits.

**Technical Enforcement:** Policy enforcement is designed to fail closed - if a policy cannot be evaluated, if required tags are missing, or if budget constraints cannot be verified, the operation is denied. No hardcoded secrets are permitted; all configuration must be via environment variables, and missing critical configuration causes startup failure rather than insecure defaults.

## 6. Multi-Cloud Neutrality

**Principle:** Governance and compliance controls should be consistent across cloud providers while respecting each platform's unique characteristics.

**Technical Enforcement:** The Codex Guardrails system provides unified controls across Azure, AWS, and GCP using OIDC-only authentication (no long-term credentials), daily drift detection, and consistent policy enforcement. Evidence artifacts are generated in standard formats (JSON, SARIF, Markdown, CSV) for independent auditing.

## 7. Economic Transparency

**Principle:** The true cost of AI operations - including compute, tokens, energy, and carbon footprint - must be measurable and attributable.

**Technical Enforcement:** The telemetry system tracks unit economics for AI inference and training with calibrated cost models. All costs are tagged by team and environment, enabling accurate attribution. Carbon intensity is calculated based on grid emissions and compute usage. These metrics are immutably logged and can be independently verified through the audit trail.

---

## Governance and Modification

These principles guide the development and deployment of the Spartan Resilience Framework. While the Apache 2.0 license permits modification and redistribution, any fork that claims to provide the same governance guarantees should maintain these core principles.

Modifications that remove audit logging, disable cryptographic verification, allow fail-open behavior in policy enforcement, or otherwise compromise the integrity guarantees may still be legal under the Apache 2.0 license, but they would no longer be the Spartan Resilience Framework as designed.

Users and organizations should verify that their deployment maintains these principles through:
- Code review of cryptographic and logging functions
- Validation of policy enforcement behavior
- Regular security audits and penetration testing
- Monitoring of audit trail integrity
- Verification of telemetry and cost calculation accuracy
