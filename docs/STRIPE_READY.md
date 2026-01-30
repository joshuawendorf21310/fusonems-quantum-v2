# Stripe Ready Checklist

Use this to get Stripe configured for patient payments, checkout sessions, and (optionally) subscriptions.

## 1. Backend environment (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_SECRET_KEY` | **Yes** | Stripe secret key (starts with `sk_test_` or `sk_live_`). From [Stripe Dashboard → API keys](https://dashboard.stripe.com/apikeys). |
| `STRIPE_WEBHOOK_SECRET` | Recommended for production | Webhook signing secret (starts with `whsec_`). From Stripe Dashboard → Webhooks → Add endpoint → Signing secret. |
| `STRIPE_PUBLISHABLE_KEY` | For frontend Payment Element | Publishable key (starts with `pk_test_` or `pk_live_`). Same Dashboard → API keys. |
| `BILLING_BRAND_NAME` | Optional | Brand name shown on checkout and receipts (default: `FusionEMS Quantum`). |

**Optional (module subscriptions):**  
`STRIPE_PRICE_ID_CAD`, `STRIPE_PRICE_ID_EPCR`, `STRIPE_PRICE_ID_BILLING`, etc., and corresponding `STRIPE_PRICE_AMOUNT_*` if you use the subscription/entitlement flow. Run `backend/scripts/stripe_setup.py` to create products and prices in Stripe, then paste the printed IDs into `.env`.

## 2. Frontend environment (root `.env`)

| Variable | Required for patient pay page | Description |
|----------|-------------------------------|-------------|
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | **Yes** for Payment Element | Same publishable key as backend (e.g. `pk_test_...`). Used by `@stripe/stripe-js` and `@stripe/react-stripe-js` on the patient pay page. |

## 3. Webhook endpoint (production)

1. In [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks), click **Add endpoint**.
2. **Endpoint URL:** `https://your-api-domain.com/api/billing/stripe/webhook`
3. **Events to send:**  
   - `checkout.session.completed`  
   - `payment_intent.succeeded`  
   - `payment_intent.payment_failed`  
   - `invoice.paid`  
   - `invoice.payment_failed`  
   - `customer.subscription.created`  
   - `customer.subscription.updated`  
   - `customer.subscription.deleted`  
   - `charge.refunded`  
   - `charge.dispute.created`  
   - `charge.dispute.closed`
4. Copy the **Signing secret** (`whsec_...`) into `STRIPE_WEBHOOK_SECRET` in `backend/.env`.

## 4. Verify readiness

- **Backend:** `GET /api/billing/stripe/ready`  
  Returns `{ "ready": true, "has_secret_key": true, "has_webhook_secret": true, "has_publishable_key": true, "message": "..." }`.  
  Use this for health checks or to confirm config before testing payments.

- **Patient pay flow:**  
  Patient Portal → Bills → Pay uses Stripe Payment Element and `POST /api/patient-portal/create-payment-intent`. Ensure backend has `STRIPE_SECRET_KEY` and frontend has `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`.

- **Checkout session flow (admin/billing):**  
  `POST /api/billing/stripe/checkout-session` creates a Stripe Checkout session for an invoice. Requires `STRIPE_SECRET_KEY`.

## 5. Test mode

Use **Test mode** in the Stripe Dashboard (toggle in the top right). Use test keys (`sk_test_...`, `pk_test_...`) and test card numbers (e.g. `4242 4242 4242 4242`). No webhook secret is required for local development if you leave `STRIPE_WEBHOOK_SECRET` empty; the webhook handler will accept unverified payloads in that case (do not do this in production).

## Quick start

```bash
# backend/.env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...   # optional for local

# .env (frontend)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

Then open `/api/billing/stripe/ready`; when `ready` is `true`, Stripe is ready for payments.
