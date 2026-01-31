"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import Link from "next/link"
import { loadStripe } from "@stripe/stripe-js"
import { Elements, PaymentElement, useStripe, useElements } from "@stripe/react-stripe-js"

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || "")

interface Bill {
  id: number
  patient_id: number
  claim_id: number
  total_amount: number
  insurance_paid: number
  patient_responsibility: number
  amount_paid: number
  balance_due: number
  status: string
  due_date: string
  created_at: string
  bill_date: string
}

function PaymentForm({ bill, onSuccess }: { bill: Bill; onSuccess: () => void }) {
  const stripe = useStripe()
  const elements = useElements()
  const [processing, setProcessing] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!stripe || !elements) {
      return
    }

    setProcessing(true)
    setErrorMessage(null)

    try {
      const { error } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/portals/patient/payments?success=true`,
        },
      })

      if (error) {
        setErrorMessage(error.message || "An error occurred during payment")
        setProcessing(false)
      } else {
        onSuccess()
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "An error occurred")
      setProcessing(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-zinc-100 mb-4">Payment Information</h3>
        <PaymentElement />
      </div>

      {errorMessage && (
        <div className="bg-red-900/20 border border-red-800 text-red-400 px-4 py-3 rounded-lg">
          <p className="font-medium">Payment Error</p>
          <p className="text-sm">{errorMessage}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || processing}
        className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-lg transition-colors font-medium"
      >
        {processing ? (
          <span className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            <span>Processing...</span>
          </span>
        ) : (
          `Pay ${new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(bill.balance_due)}`
        )}
      </button>
    </form>
  )
}

export default function PaymentPage() {
  const router = useRouter()
  const params = useParams()
  const { user, logout } = useAuth()
  const [bill, setBill] = useState<Bill | null>(null)
  const [clientSecret, setClientSecret] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const billId = params.id

  useEffect(() => {
    if (billId) {
      fetchBill()
    }
  }, [billId])

  const fetchBill = async () => {
    try {
      setLoading(true)
      setError(null)

      const billResponse = await fetch(`http://localhost:8000/api/patient-portal/bills/${billId}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!billResponse.ok) {
        throw new Error("Failed to fetch bill details")
      }

      const billData = await billResponse.json()
      setBill(billData)

      const paymentIntentResponse = await fetch("http://localhost:8000/api/patient-portal/create-payment-intent", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          bill_id: billId,
          amount: billData.balance_due,
        }),
      })

      if (!paymentIntentResponse.ok) {
        throw new Error("Failed to create payment intent")
      }

      const paymentData = await paymentIntentResponse.json()
      setClientSecret(paymentData.client_secret)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    localStorage.removeItem("portal")
    router.push("/")
  }

  const handlePaymentSuccess = () => {
    router.push("/portals/patient/payments?success=true")
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Patient Portal</h1>
          <p className="text-sm text-zinc-400">FusionEMS Quantum</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm font-semibold text-zinc-100">{user?.full_name || "User"}</p>
            <p className="text-xs text-zinc-400">{user?.organization_name || "Organization"}</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>

      <nav className="bg-zinc-900 border-b border-zinc-800 px-6 py-3">
        <div className="flex space-x-6">
          <Link href="/portals/patient/dashboard" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
            Dashboard
          </Link>
          <Link href="/portals/patient/bills" className="text-sm text-zinc-100 font-medium border-b-2 border-blue-500 pb-3">
            Bills
          </Link>
          <Link href="/portals/patient/payments" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
            Payment History
          </Link>
          <Link href="/portals/patient/profile" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
            Profile
          </Link>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="mb-6">
          <Link href={`/portals/patient/bills/${billId}`} className="text-sm text-blue-400 hover:text-blue-300 flex items-center space-x-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back to Bill Details</span>
          </Link>
        </div>

        <div className="mb-8">
          <h2 className="text-3xl font-bold text-zinc-100 mb-2">Make a Payment</h2>
          <p className="text-zinc-400">Securely pay your medical bill</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-800 text-red-400 px-4 py-3 rounded-lg">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : bill && clientSecret ? (
          <div className="space-y-6">
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-zinc-100 mb-4">Bill Summary</h3>
              <div className="space-y-3">
                <div className="flex justify-between py-2">
                  <span className="text-zinc-400">Bill Number</span>
                  <span className="text-zinc-100 font-medium">#{bill.id}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-zinc-400">Due Date</span>
                  <span className="text-zinc-100 font-medium">{formatDate(bill.due_date)}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-zinc-400">Patient Responsibility</span>
                  <span className="text-zinc-100 font-medium">{formatCurrency(bill.patient_responsibility)}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-zinc-400">Amount Paid</span>
                  <span className="text-green-400 font-medium">{formatCurrency(bill.amount_paid)}</span>
                </div>
                <div className="flex justify-between py-3 border-t-2 border-zinc-700">
                  <span className="text-lg font-semibold text-zinc-100">Amount Due</span>
                  <span className="text-lg font-bold text-zinc-100">{formatCurrency(bill.balance_due)}</span>
                </div>
              </div>
            </div>

            <Elements stripe={stripePromise} options={{ clientSecret }}>
              <PaymentForm bill={bill} onSuccess={handlePaymentSuccess} />
            </Elements>

            <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <svg className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-blue-400 mb-1">Secure Payment</p>
                  <p className="text-xs text-zinc-400">
                    Your payment information is encrypted and processed securely through Stripe. We never store your payment details.
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-8 text-center">
            <h3 className="text-xl font-semibold text-zinc-100 mb-2">Unable to Process Payment</h3>
            <p className="text-zinc-400">There was an issue loading the payment form. Please try again later.</p>
          </div>
        )}
      </main>
    </div>
  )
}
