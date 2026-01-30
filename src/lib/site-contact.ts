/**
 * Central contact info for billing/support.
 * Founder email (joshua.j.wendorf@fusionemsquantum.com) is configured in backend; aliases below for display/links.
 */
export const BILLING_EMAIL =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_BILLING_EMAIL
    ? process.env.NEXT_PUBLIC_BILLING_EMAIL
    : "billing@fusionemsquantum.com"
export const SUPPORT_EMAIL =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_SUPPORT_EMAIL
    ? process.env.NEXT_PUBLIC_SUPPORT_EMAIL
    : "billing@fusionemsquantum.com"
export const BILLING_PHONE =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_BILLING_PHONE
    ? process.env.NEXT_PUBLIC_BILLING_PHONE
    : "+1 (715) 254-3027"
