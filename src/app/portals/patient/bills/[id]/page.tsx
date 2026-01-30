"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import Link from "next/link"
import { BILLING_EMAIL, BILLING_PHONE } from "@/lib/site-contact"

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

export default function BillDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { user, logout } = useAuth()
  const [bill, setBill] = useState<Bill | null>(null)
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
      const response = await fetch(`http://localhost:8000/api/patient-portal/bills/${billId}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch bill details")
      }

      const data = await response.json()
      setBill(data)
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
      case "paid":
        return "bg-green-900/20 text-green-400 border-green-800"
      case "pending":
        return "bg-yellow-900/20 text-yellow-400 border-yellow-800"
      case "overdue":
        return "bg-red-900/20 text-red-400 border-red-800"
      case "partial":
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

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="mb-6">
          <Link href="/portals/patient/bills" className="text-sm text-blue-400 hover:text-blue-300 flex items-center space-x-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back to Bills</span>
          </Link>
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
        ) : bill ? (
          <div className="space-y-6">
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center space-x-3 mb-3">
                    <h2 className="text-2xl font-bold text-zinc-100">Bill #{bill.id}</h2>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(bill.status)}`}>
                      {bill.status}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-zinc-400">Bill Date: {formatDate(bill.bill_date)}</p>
                    <p className="text-sm text-zinc-400">Due Date: {formatDate(bill.due_date)}</p>
                    <p className="text-sm text-zinc-400">Claim ID: {bill.claim_id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-zinc-400 mb-2">Balance Due</p>
                  <p className="text-4xl font-bold text-zinc-100">{formatCurrency(bill.balance_due)}</p>
                </div>
              </div>

              <div className="border-t border-zinc-800 pt-6">
                <h3 className="text-lg font-semibold text-zinc-100 mb-4">Bill Summary</h3>
                <div className="space-y-3">
                  <div className="flex justify-between py-2">
                    <span className="text-zinc-400">Total Amount</span>
                    <span className="text-zinc-100 font-medium">{formatCurrency(bill.total_amount)}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-zinc-400">Insurance Paid</span>
                    <span className="text-green-400 font-medium">-{formatCurrency(bill.insurance_paid)}</span>
                  </div>
                  <div className="flex justify-between py-2 border-t border-zinc-800">
                    <span className="text-zinc-400">Patient Responsibility</span>
                    <span className="text-zinc-100 font-medium">{formatCurrency(bill.patient_responsibility)}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-zinc-400">Amount Paid</span>
                    <span className="text-green-400 font-medium">-{formatCurrency(bill.amount_paid)}</span>
                  </div>
                  <div className="flex justify-between py-3 border-t-2 border-zinc-700">
                    <span className="text-lg font-semibold text-zinc-100">Balance Due</span>
                    <span className="text-lg font-bold text-zinc-100">{formatCurrency(bill.balance_due)}</span>
                  </div>
                </div>
              </div>

              {bill.balance_due > 0 && bill.status.toLowerCase() !== "paid" && (
                <div className="border-t border-zinc-800 pt-6 mt-6">
                  <Link
                    href={`/portals/patient/bills/${bill.id}/pay`}
                    className="w-full block text-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                  >
                    Pay Now - {formatCurrency(bill.balance_due)}
                  </Link>
                </div>
              )}
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-zinc-100 mb-4">Additional Information</h3>
              <div className="space-y-3 text-sm">
                <p className="text-zinc-400">
                  If you have questions about this bill, please contact our billing department at{" "}
                  <a href={`tel:${BILLING_PHONE.replace(/\D/g, "")}`} className="text-blue-400 hover:text-blue-300">
                    {BILLING_PHONE}
                  </a>
                  {" "}or{" "}
                  <a href={`mailto:${BILLING_EMAIL}`} className="text-blue-400 hover:text-blue-300">
                    {BILLING_EMAIL}
                  </a>
                  .
                </p>
                <p className="text-zinc-400">
                  For payment assistance or to set up a payment plan, please call our financial counselors.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-8 text-center">
            <h3 className="text-xl font-semibold text-zinc-100 mb-2">Bill Not Found</h3>
            <p className="text-zinc-400">The requested bill could not be found.</p>
          </div>
        )}
      </main>
    </div>
  )
}
