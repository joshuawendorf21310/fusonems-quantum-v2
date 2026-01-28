"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import Link from "next/link"

interface Payment {
  id: number
  bill_id: number
  patient_id: number
  amount: number
  payment_method: string
  payment_status: string
  transaction_id: string
  payment_date: string
  created_at: string
}

export default function PaymentsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, logout } = useAuth()
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showSuccess, setShowSuccess] = useState(false)

  useEffect(() => {
    if (searchParams.get("success") === "true") {
      setShowSuccess(true)
      setTimeout(() => setShowSuccess(false), 5000)
    }
    fetchPayments()
  }, [searchParams])

  const fetchPayments = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch("http://localhost:8000/api/patient-portal/payments", {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch payments")
      }

      const data = await response.json()
      setPayments(data)
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

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
      case "success":
        return "bg-green-900/20 text-green-400 border-green-800"
      case "pending":
        return "bg-yellow-900/20 text-yellow-400 border-yellow-800"
      case "failed":
        return "bg-red-900/20 text-red-400 border-red-800"
      case "refunded":
        return "bg-blue-900/20 text-blue-400 border-blue-800"
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700"
    }
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
      month: "short",
      day: "numeric",
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
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
          <Link href="/portals/patient/bills" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
            Bills
          </Link>
          <Link href="/portals/patient/payments" className="text-sm text-zinc-100 font-medium border-b-2 border-blue-500 pb-3">
            Payment History
          </Link>
          <Link href="/portals/patient/profile" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
            Profile
          </Link>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-zinc-100 mb-2">Payment History</h2>
          <p className="text-zinc-400">View all your past payments</p>
        </div>

        {showSuccess && (
          <div className="mb-6 bg-green-900/20 border border-green-800 text-green-400 px-4 py-3 rounded-lg">
            <p className="font-medium">Payment Successful</p>
            <p className="text-sm">Your payment has been processed successfully.</p>
          </div>
        )}

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
        ) : payments.length === 0 ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-8 text-center">
            <svg className="w-16 h-16 text-zinc-700 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            <h3 className="text-xl font-semibold text-zinc-100 mb-2">No Payments Found</h3>
            <p className="text-zinc-400 mb-4">You haven't made any payments yet.</p>
            <Link
              href="/portals/patient/bills"
              className="inline-block px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              View Bills
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {payments.map((payment) => (
              <div
                key={payment.id}
                className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 hover:border-zinc-700 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-zinc-100">Payment #{payment.id}</h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(payment.payment_status)}`}>
                        {payment.payment_status}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-400">Date: {formatDateTime(payment.payment_date)}</p>
                    <p className="text-sm text-zinc-400">Transaction ID: {payment.transaction_id}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-zinc-400 mb-1">Amount</p>
                    <p className="text-2xl font-bold text-zinc-100">{formatCurrency(payment.amount)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 pb-4 border-b border-zinc-800">
                  <div>
                    <p className="text-xs text-zinc-500 mb-1">Bill ID</p>
                    <Link
                      href={`/portals/patient/bills/${payment.bill_id}`}
                      className="text-sm font-medium text-blue-400 hover:text-blue-300"
                    >
                      #{payment.bill_id}
                    </Link>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 mb-1">Payment Method</p>
                    <p className="text-sm font-medium text-zinc-100 capitalize">{payment.payment_method}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 mb-1">Status</p>
                    <p className="text-sm font-medium text-zinc-100 capitalize">{payment.payment_status}</p>
                  </div>
                </div>

                <div className="flex space-x-3 mt-4">
                  <Link
                    href={`/portals/patient/bills/${payment.bill_id}`}
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors text-sm font-medium"
                  >
                    View Bill
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
