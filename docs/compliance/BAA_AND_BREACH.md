# Business Associate Agreements (BAA) & Breach Notification

**FusionEMS Quantum — HIPAA Operations**  
**Last updated:** January 30, 2026

---

## 1. Business Associate Agreements (BAA)

Under HIPAA, we must have a signed **Business Associate Agreement (BAA)** with any vendor that creates, receives, maintains, or transmits **Protected Health Information (PHI)** on our behalf.

### Vendors requiring BAA (tracking)

| Vendor | Service | BAA status | Notes |
|--------|---------|------------|--------|
| **Stripe** | Payment processing | ☐ Obtain / ☐ Signed | Payments may touch PHI identifiers; use Stripe BAA. |
| **Telnyx** | Voice, SMS, fax | ☐ Obtain / ☐ Signed | Call/SMS may contain PHI; require BAA. |
| **Postmark** (optional) | Transactional email | ☐ Obtain / ☐ Signed | If used for patient-facing email. |
| **Metriport** | Patient information (FHIR) | ☐ Obtain / ☐ Signed | Patient info source; BAA required. |
| **DigitalOcean** (Spaces) | Object storage | ☐ Obtain / ☐ Signed | File storage for PHI; check DO BAA availability. |
| **Lob** (if used) | Mail / print | ☐ Obtain / ☐ Signed | If patient statements mailed. |

### Actions

1. **Founder/Compliance:** Request BAA from each vendor above before processing PHI.
2. **Store:** Keep signed BAAs in a secure, auditable location (e.g. Founder documents, legal folder).
3. **Review:** Re-check BAA status when adding new integrations (APIs, email, storage, telephony).
4. **Dashboard (future):** Add a BAA status widget to Founder Compliance (e.g. `/founder/compliance/baa`) listing vendor, status, renewal date.

---

## 2. Breach Notification Workflow

HIPAA requires notification of **breaches of unsecured PHI** within specific timeframes.

### Definitions

- **Breach:** Unauthorized acquisition, access, use, or disclosure of PHI that compromises security or privacy.
- **Unsecured PHI:** PHI not rendered unusable, unreadable, or indecipherable to unauthorized persons (e.g. encryption at rest + in transit).

### Timeline (summary)

| Recipient | Deadline |
|-----------|----------|
| **Affected individuals** | Without unreasonable delay, no later than **60 days** after discovery. |
| **HHS (Department of Health and Human Services)** | If 500+ individuals: **60 days**. If &lt;500: **annual submission** (by 60 days after end of calendar year). |
| **Media** (if 500+ in same jurisdiction) | Without unreasonable delay, no later than **60 days**. |

### Internal workflow (steps)

1. **Discover & contain**  
   - Identify scope (what PHI, how many individuals, how it was exposed).  
   - Contain the breach (revoke access, patch, isolate).

2. **Assemble team**  
   - Privacy Officer / Compliance, Legal, Founder, IT.  
   - Designate a single point for external communication.

3. **Assess risk**  
   - Document low-probability exception if applicable (e.g. good-faith acquisition, no retention).  
   - If not low probability → treat as breach and proceed with notifications.

4. **Notify individuals**  
   - By first-class mail (or email if individual agreed).  
   - Content: what happened, what PHI was involved, what they should do, contact for questions, what we are doing.

5. **Notify HHS**  
   - **500+ individuals:** [OCR breach portal](https://ocrportal.hhs.gov/ocr/breach/wizard_breach.jsf) within 60 days.  
   - **&lt;500:** Log and submit annually (same portal).

6. **Media**  
   - If 500+ in same state/jurisdiction: notify prominent media in that jurisdiction per HIPAA rule.

7. **Document**  
   - Retain all documentation (discovery date, scope, risk assessment, copies of notices, HHS submission) for at least **6 years**.

### Where to document in-platform

- **Founder / Compliance:** Use incident tracking or a dedicated “Breach log” (e.g. date, description, scope, notifications sent, HHS submission).  
- **Audit trail:** All access to PHI is already logged; use existing audit logs as evidence in breach investigation.

---

## 3. References

- HHS HIPAA Breach Notification Rule: [https://www.hhs.gov/hipaa/for-professionals/breach-notification](https://www.hhs.gov/hipaa/for-professionals/breach-notification)
- OCR Breach Reporting: [https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)

---

*This document is part of FusionEMS Quantum compliance operations. For BAA tracking and breach log implementation, see Founder Compliance and FORENSIC_SYSTEM_AUDIT.md.*
