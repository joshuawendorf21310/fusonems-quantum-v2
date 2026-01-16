# Stripe Guardrails

## PHI Safety
- Never transmit PHI to Stripe.
- Only send internal IDs in metadata: `org_id`, `invoice_id`, `invoice_number`.
- No patient names, DOBs, or clinical details in Stripe objects.

## Idempotency
- Webhooks are idempotent by `event_id`.
- Payment creation should include idempotency keys (e.g., invoice_id + amount).

## Stripe Is Not The Invoice Brain
- Internal invoices and ledger entries are authoritative.
- Stripe invoices are optional and never replace internal billing state.

## Environment Separation
- Enforce `STRIPE_ENV` = `test` or `live`.
- Prevent live keys in non-production.

## Subscription Drift Prevention
- Subscription events update feature flags per org.
- Optional enforcement can disable modules when subscriptions lapse.

## Audit & Canonical Events
- Every payment mutation writes audit logs + emits canonical events.

## ACH / Check / Patient Portal Rules
- **ACH**: Enable for agency subscriptions once average monthly invoices exceed ~$1k. Use Stripe ACH for agencies first.
- **Checks**: Record manual payments internally (provider=check), require dual approval for high amounts, no Stripe usage.
- **Patient Portal**: Add when patient responsibility payments become recurring; use invoice token lookup + Stripe Checkout.
