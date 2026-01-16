# Stripe + Office Ally Flow

## Overview
Insurance claims flow through Office Ally for 837P/835/ERA and remain authoritative inside FusionEMS. Stripe is used for agency subscriptions and patient responsibility payments only.

## ASCII Flow Diagram

```
                 INSURANCE CLAIM PATH (OFFICE ALLY)
  ePCR -> Coding -> 837P -> Office Ally -> Payer
           |                          |
           |                        835/ERA
           v                          v
     Internal Invoice <--- Adjudication/Posting
           |
           | Patient Responsibility?
           v
    Patient Invoice + Balance Due
           |
           v
     Patient Portal (Stripe Checkout)
           |
           v
   Stripe Webhook -> Billing Ledger -> Status Updated
```

## Explanation
- **Insurance claims**: ePCR data is coded, exported as 837P, submitted via Office Ally, and adjudicated via 835/ERA. The platform remains the source of truth.
- **Patient responsibility**: After adjudication, the internal invoice moves to `PATIENT_INVOICED`. Stripe handles payment collection via Checkout/PaymentIntent, and webhooks update internal ledger + invoice status.
- **No PHI in Stripe**: Only internal IDs (org_id, invoice_id, invoice_number) are used in Stripe metadata.
