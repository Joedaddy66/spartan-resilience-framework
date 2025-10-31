# Statement of Work
## Codex Scroll Validation System - 25-Hour Gauntlet Pilot

**Date:** [Insert Date]  
**Client:** [Client Organization Name]  
**Vendor:** [Your Organization Name]  
**Engagement Period:** 25 Hours from Project Kickoff

---

## 1. Engagement Overview

This Statement of Work ("SOW") defines the scope, deliverables, timeline, and compensation for the Codex Scroll Validation System pilot implementation (the "25-Hour Gauntlet"). The objective is to deploy a fully operational, auditable multi-tier validation pipeline using the Client's actual data within a fixed 25-hour engagement period.

## 2. Scope of Work

### In Scope:
- **System Deployment**: Installation and configuration of the Codex scroll validation system on Client-provided infrastructure or cloud environment
- **Data Integration**: Connection to Client's existing data sources and ingestion of real production or staging data
- **Tier Implementation**: Activation of all three validation tiers:
  - **T0 (Spartans)**: Schema validation, content hashing, basic fact checking
  - **T1 (Sentinels)**: Policy enforcement and compliance validation
  - **T2 (Council)**: Final review and approval workflow
- **API Configuration**: Setup of REST API endpoints with authentication (`CODEX_API_KEY`)
- **Audit Trail Setup**: Configuration of immutable ledger with SHA-256 content hashing for compliance requirements
- **Documentation**: Provision of Technical Architecture Briefing and Pilot Quickstart Guide
- **Knowledge Transfer**: 2-hour technical walkthrough with Client's engineering team

### Out of Scope:
- Production-grade cryptographic signatures (ed25519) - available in follow-on engagement
- Custom UI development beyond standard API interface
- Integration with third-party systems not identified during kickoff
- Training beyond the included 2-hour technical walkthrough
- Ongoing support or maintenance beyond pilot completion

## 3. Deliverables

Upon successful completion of the 25-Hour Gauntlet, Client will receive:

1. **Running Codex System**: Fully operational validation pipeline processing Client data
2. **API Access**: Production-ready REST API with authentication and rate limiting
3. **Audit Ledger**: Immutable record of all validation transactions with content hashes
4. **Technical Documentation**:
   - Technical Architecture Briefing
   - Pilot Quickstart Guide (API integration)
   - Scroll Format Specification
   - System Configuration Guide
5. **Source Code**: Complete codebase with MIT or Apache 2.0 license
6. **Deployment Package**: Container images or VM configuration for replication
7. **Test Results**: Validation reports showing successful processing of Client data samples

## 4. Timeline

**Total Engagement:** 25 Hours  
**Expected Completion:** 3-5 business days from kickoff

### Milestones:
- **Hour 0-4**: Environment setup, data source connection
- **Hour 5-12**: T0/T1/T2 tier configuration and validation rule implementation
- **Hour 13-20**: API deployment, testing with Client data, audit trail verification
- **Hour 21-23**: Documentation finalization, edge case testing
- **Hour 24-25**: Technical walkthrough and knowledge transfer

Client will receive progress updates at Hours 8, 16, and 24.

## 5. Client Responsibilities

To ensure successful delivery within the 25-hour window, Client agrees to:

1. **Timely Access**: Provide infrastructure access (cloud credentials, VPN, etc.) within 2 hours of kickoff
2. **Data Availability**: Supply representative data samples and schemas at project start
3. **Stakeholder Availability**: Ensure technical point-of-contact is available for questions (response time < 4 hours)
4. **Environment Readiness**: Confirm deployment environment meets minimum requirements:
   - Python 3.12+ runtime
   - 2GB RAM minimum
   - Network connectivity for API access
5. **Decision Authority**: Technical point-of-contact has authority to approve validation rules and policies

Delays caused by Client unavailability or environment issues may extend the calendar time for completion beyond 3-5 business days, though engagement will remain capped at 25 billable hours.

## 6. Acceptance Criteria

The pilot will be considered successfully completed when:

1. ✅ Client can submit scrolls via API and receive validation responses
2. ✅ All three tiers (T0, T1, T2) process at least 10 sample Client scrolls
3. ✅ Audit ledger correctly records all transactions with content hashes
4. ✅ API authentication and rate limiting function as documented
5. ✅ Client technical team completes knowledge transfer session

Client will have 5 business days from delivery to confirm acceptance or identify deficiencies. Any issues identified will be resolved within the original 25-hour engagement allocation.

## 7. Compensation

**Fixed Fee:** $[Insert Amount] USD

**Payment Terms:**
- **Net 30** from invoice date
- Invoice will be issued upon successful completion and Client acceptance
- Payment via wire transfer, ACH, or check
- No partial payments or deposits required

**What's Included:**
- All 25 hours of engineering time
- All deliverables listed in Section 3
- Technical support during the pilot period
- One round of minor revisions within 30 days of delivery

**What's Extra:**
- Additional customization requests beyond scope: $[Rate]/hour
- Post-pilot ongoing support: Available via separate maintenance agreement
- Production cryptographic signing: Available as add-on module

## 8. Intellectual Property

- **Client Data**: Remains Client's exclusive property. Vendor will not retain copies post-engagement.
- **Codex System Code**: Licensed to Client under MIT License (or Apache 2.0 at Client's preference)
- **Custom Configurations**: Client-specific validation rules and policies are Client property
- **Generic Framework**: Vendor retains right to use Codex framework for other clients

## 9. Confidentiality

Both parties agree to maintain confidentiality of proprietary information exchanged during the engagement. Vendor will not disclose Client identity or use case without prior written consent. Client may reference Vendor as service provider in compliance documentation.

## 10. Limitation of Liability

This is a pilot engagement. The System is provided "as-is" for evaluation purposes. Vendor's liability is limited to the fees paid under this SOW. Vendor is not liable for data loss, business interruption, or consequential damages. Client is responsible for backup of all data processed through the System.

## 11. Termination

Either party may terminate this SOW with written notice. If Client terminates:
- Prior to Hour 12: 50% of fixed fee due
- After Hour 12: 100% of fixed fee due

If Vendor terminates due to Client breach (e.g., failure to provide access), no fees are due.

## 12. Signature Authority

By signing below, both parties agree to the terms and conditions outlined in this Statement of Work.

---

**CLIENT:**

Signature: ________________________________  
Printed Name: ________________________________  
Title: ________________________________  
Date: ________________________________

**VENDOR:**

Signature: ________________________________  
Printed Name: ________________________________  
Title: ________________________________  
Date: ________________________________

---

## Appendix A: Technical Requirements

**Minimum Infrastructure:**
- Linux/Unix environment (Ubuntu 22.04+ or equivalent)
- Python 3.12+
- 2GB RAM, 10GB storage
- Outbound HTTPS access
- (Optional) Docker/Podman for containerized deployment

**Dependencies:**
- LangGraph >= 0.2.35
- Pydantic >= 2.7
- FastAPI (for API layer)
- PostgreSQL or SQLite (for audit ledger persistence)

**Network Requirements:**
- API endpoint accessible via HTTPS
- TLS 1.2+ certificate (can be self-signed for pilot)
- Rate limiting: 100 req/min recommended

---

**Questions?** Contact [Your Email] or [Your Phone]

**Ready to begin?** Return signed SOW to initiate engagement within 48 hours.
