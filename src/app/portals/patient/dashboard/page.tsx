"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import Link from "next/link"

interface Bill {
  id: number
  total_amount: number
  balance_due: number
  status: string
  due_date: string
}

interface Payment {
  id: number
  amount: number
  payment_date: string
  payment_status: string
}

interface DashboardStats {
  total_bills: number
  pending_amount: number
  paid_amount: number
  upcoming_bills: number
}

export default function PatientDashboard() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentBills, setRecentBills] = useState<Bill[]>([])
  const [recentPayments, setRecentPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)

      const [billsRes, paymentsRes] = await Promise.all([
        fetch("http://localhost:8000/api/patient-portal/bills", {
          credentials: "include",
          headers: { "Content-Type": "application/json" },
        }),
        fetch("http://localhost:8000/api/patient-portal/payments", {
          credentials: "include",
          headers: { "Content-Type": "application/json" },
        }),
      ])

      if (billsRes.ok) {
        const bills = await billsRes.json()
        setRecentBills(bills.slice(0, 3))
        
        const totalBills = bills.length
        const pendingAmount = bills
          .filter((b: Bill) => b.status !== "paid")
          .reduce((sum: number, b: Bill) => sum + b.balance_due, 0)
        const paidAmount = bills
          .filter((b: Bill) => b.status === "paid")
          .reduce((sum: number, b: Bill) => sum + b.total_amount, 0)
        const upcomingBills = bills.filter((b: Bill) => b.status === "pending").length

        setStats({ total_bills: totalBills, pending_amount: pendingAmount, paid_amount: paidAmount, upcoming_bills: upcomingBills })
      }

      if (paymentsRes.ok) {
        const payments = await paymentsRes.json()
        setRecentPayments(payments.slice(0, 3))
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    localStorage.removeItem("portal")
    router.push("/")
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

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "paid":
      case "completed":
        return "bg-green-900/20 text-green-400 border-green-800"
      case "pending":
        return "bg-yellow-900/20 text-yellow-400 border-yellow-800"
      case "overdue":
        return "bg-red-900/20 text-red-400 border-red-800"
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700"
    }
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
          <Link href="/portals/patient/dashboard" className="text-sm text-zinc-100 font-medium border-b-2 border-blue-500 pb-3">
            Dashboard
          </Link>
          <Link href="/portals/patient/bills" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
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

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-zinc-100 mb-2">Welcome Back</h2>
          <p className="text-zinc-400">Manage your bills, payments, and account information</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-4 gap-6 mb-8">
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-zinc-400">Total Bills</p>
                  <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-2xl font-bold text-zinc-100">{stats?.total_bills || 0}</p>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-zinc-400">Pending Amount</p>
                  <svg className="w-5 h-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-2xl font-bold text-zinc-100">{formatCurrency(stats?.pending_amount || 0)}</p>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-zinc-400">Total Paid</p>
                  <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-2xl font-bold text-zinc-100">{formatCurrency(stats?.paid_amount || 0)}</p>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-zinc-400">Upcoming Bills</p>
                  <svg className="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-2xl font-bold text-zinc-100">{stats?.upcoming_bills || 0}</p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-zinc-100">Recent Bills</h3>
                  <Link href="/portals/patient/bills" className="text-sm text-blue-400 hover:text-blue-300">
                    View All →
                  </Link>
                </div>
                {recentBills.length === 0 ? (
                  <p className="text-zinc-400 text-sm text-center py-4">No bills found</p>
                ) : (
                  <div className="space-y-4">
                    {recentBills.map((bill) => (
                      <div key={bill.id} className="flex items-center justify-between py-3 border-b border-zinc-800 last:border-0">
                        <div>
                          <p className="text-sm font-medium text-zinc-100">Bill #{bill.id}</p>
                          <p className="text-xs text-zinc-400">{formatDate(bill.due_date)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-zinc-100">{formatCurrency(bill.balance_due)}</p>
                          <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(bill.status)}`}>
                            {bill.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-zinc-100">Recent Payments</h3>
                  <Link href="/portals/patient/payments" className="text-sm text-blue-400 hover:text-blue-300">
                    View All →
                  </Link>
                </div>
                {recentPayments.length === 0 ? (
                  <p className="text-zinc-400 text-sm text-center py-4">No payments found</p>
                ) : (
                  <div className="space-y-4">
                    {recentPayments.map((payment) => (
                      <div key={payment.id} className="flex items-center justify-between py-3 border-b border-zinc-800 last:border-0">
                        <div>
                          <p className="text-sm font-medium text-zinc-100">Payment #{payment.id}</p>
                          <p className="text-xs text-zinc-400">{formatDate(payment.payment_date)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-green-400">{formatCurrency(payment.amount)}</p>
                          <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(payment.payment_status)}`}>
                            {payment.payment_status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <Link
                href="/portals/patient/bills"
                className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-lg p-6 transition-colors"
              >
                <div className="w-12 h-12 bg-blue-900/20 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-zinc-100 mb-2">View Bills</h3>
                <p className="text-sm text-zinc-400">View and pay your medical bills</p>
              </Link>

              <Link
                href="/portals/patient/payments"
                className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-lg p-6 transition-colors"
              >
                <div className="w-12 h-12 bg-green-900/20 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-zinc-100 mb-2">Payment History</h3>
                <p className="text-sm text-zinc-400">View all your past payments</p>
              </Link>

              <Link
                href="/portals/patient/profile"
                className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-lg p-6 transition-colors"
              >
                <div className="w-12 h-12 bg-purple-900/20 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-zinc-100 mb-2">My Profile</h3>
                <p className="text-sm text-zinc-400">Manage your personal information</p>
              </Link>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
