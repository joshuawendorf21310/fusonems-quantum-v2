"use client"

import { useEffect, useState } from "react"
import Sidebar from "@/components/layout/Sidebar"
import Topbar from "@/components/layout/Topbar"
import { apiFetch } from "@/lib/api"

interface ThirdPartyAgency {
  id: number
  agency_name: string
  contact_email: string
  onboarding_status: string
  onboarding_progress: number
  activated_at: string | null
  total_accounts: number
  active_accounts: number
  messages_pending: number
  state?: string
  service_types?: string[]  // "ambulance" | "fire" | "hems"
  base_charge_cents?: number | null
  per_call_cents?: number | null
  billing_interval?: string
}

interface AgencyMessage {
  id: number
  agency_id: number
  agency_name: string
  subject: string
  message_body: string
  category: string
  priority: string
  ai_triaged: boolean
  ai_suggested_response: string | null
  status: string
  created_at: string
}

interface AgencyAnalytics {
  agency_id: number
  agency_name: string
  total_statements_sent: number
  total_collected: number
  collection_rate: number
  avg_days_to_payment: number
  active_payment_plans: number
}

export default function AgencyPortalDashboard() {
  const [agencies, setAgencies] = useState<ThirdPartyAgency[]>([])
  const [messages, setMessages] = useState<AgencyMessage[]>([])
  const [analytics, setAnalytics] = useState<AgencyAnalytics[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAgencyData()
    const interval = setInterval(fetchAgencyData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchAgencyData = async () => {
    try {
      const [agenciesData, messagesData, analyticsData] = await Promise.all([
        apiFetch<ThirdPartyAgency[]>("/api/agency/agencies"),
        apiFetch<AgencyMessage[]>("/api/agency/messages?status=pending&all=true"),
        apiFetch<AgencyAnalytics[]>("/api/agency/analytics")
      ])
      setAgencies(agenciesData)
      setMessages(Array.isArray(messagesData) ? messagesData : [])
      setAnalytics(analyticsData)
      setLoading(false)
    } catch (err) {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "—"
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const getOnboardingColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: "bg-yellow-700 text-yellow-300",
      in_progress: "bg-blue-700 text-blue-300",
      completed: "bg-green-700 text-green-300",
      activated: "bg-purple-700 text-purple-300"
    }
    return colors[status] || colors.pending
  }

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: "bg-gray-700 text-gray-300",
      medium: "bg-yellow-700 text-yellow-300",
      high: "bg-red-700 text-red-300"
    }
    return colors[priority] || colors.low
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a]">
        <Sidebar />
        <main className="ml-64">
          <Topbar />
          <div className="p-6">
            <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
              <div className="flex flex-col items-center gap-4">
                <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-gray-400">Loading agency portal...</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  const activeAgencies = agencies.filter(a => a.onboarding_status === "activated")
  const pendingMessages = messages.filter(m => m.status === "pending")
  const aiTriagedMessages = messages.filter(m => m.ai_triaged)

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Sidebar />
      <main className="ml-64">
        <Topbar />
        <div className="p-6">
          <section className="space-y-6">
            <header className="mb-8">
              <p className="text-xs uppercase tracking-wider text-orange-500 font-semibold mb-2">
                Third-Party Billing Agency Portal
              </p>
              <h2 className="text-3xl font-bold text-white mb-2">Multi-Agency Management</h2>
              <p className="text-gray-400 mb-2">
                Ambulance, Fire & HEMS billing—10-step onboarding, AI-powered messaging, operational analytics, and complete agency isolation.
              </p>
              <div className="flex flex-wrap gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-orange-500/20 text-orange-300 border border-orange-500/30">Ambulance</span>
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-orange-500/20 text-orange-300 border border-orange-500/30">Fire</span>
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-orange-500/20 text-orange-300 border border-orange-500/30">HEMS</span>
              </div>
              <p className="text-orange-200/90 text-sm">
                We started in Wisconsin; we're built to scale nationwide. Fair pricing: base + per transport—state by state.
              </p>
            </header>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-900 border border-green-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Active Agencies</p>
                <p className="text-white text-2xl font-bold">{activeAgencies.length}</p>
              </div>
              <div className="bg-gray-900 border border-blue-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Total Agencies</p>
                <p className="text-white text-2xl font-bold">{agencies.length}</p>
              </div>
              <div className="bg-gray-900 border border-yellow-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">Pending Messages</p>
                <p className="text-white text-2xl font-bold">{pendingMessages.length}</p>
              </div>
              <div className="bg-gray-900 border border-purple-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm mb-1">AI Triaged</p>
                <p className="text-white text-2xl font-bold">{aiTriagedMessages.length}</p>
              </div>
            </div>

            {/* Agency List */}
            <section className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden mb-6">
              <div className="p-6 border-b border-gray-800">
                <h3 className="text-xl font-bold text-white">Billing Agencies</h3>
                <p className="text-gray-400 text-sm mt-1">
                  10-step onboarding: Agency Info → Authorized Contact → Billing Authorization → Consent Capture → Configuration → Review → Activation
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-950 border-b border-gray-800">
                    <tr>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Agency Name</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">State</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Service Types</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Contact Email</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Onboarding Status</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Progress</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Total Accounts</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Active Accounts</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Pending Messages</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Activated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agencies.map((agency) => (
                      <tr key={agency.id} className="border-b border-gray-800 hover:bg-gray-800 transition cursor-pointer">
                        <td className="p-4 text-white font-semibold">{agency.agency_name}</td>
                        <td className="p-4 text-gray-300 text-sm font-medium">{agency.state || "—"}</td>
                        <td className="p-4">
                          {(agency.service_types && agency.service_types.length > 0) ? (
                            <div className="flex flex-wrap gap-1">
                              {agency.service_types.map((t) => (
                                <span key={t} className="px-2 py-0.5 rounded text-xs font-medium bg-gray-700 text-gray-300 capitalize">
                                  {t}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-gray-500 text-sm">—</span>
                          )}
                        </td>
                        <td className="p-4 text-gray-400 text-sm">{agency.contact_email}</td>
                        <td className="p-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getOnboardingColor(agency.onboarding_status)}`}>
                            {agency.onboarding_status.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-700 rounded-full h-2 max-w-[100px]">
                              <div 
                                className="bg-blue-500 h-2 rounded-full"
                                style={{ width: `${agency.onboarding_progress}%` }}
                              />
                            </div>
                            <span className="text-gray-400 text-xs">{agency.onboarding_progress}%</span>
                          </div>
                        </td>
                        <td className="p-4 text-white text-sm">{agency.total_accounts}</td>
                        <td className="p-4 text-white text-sm">{agency.active_accounts}</td>
                        <td className="p-4">
                          {agency.messages_pending > 0 ? (
                            <span className="px-2 py-1 bg-yellow-700 text-yellow-300 rounded text-xs font-medium">
                              {agency.messages_pending}
                            </span>
                          ) : (
                            <span className="text-gray-500 text-sm">—</span>
                          )}
                        </td>
                        <td className="p-4 text-gray-400 text-sm">{formatDate(agency.activated_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {agencies.length === 0 && (
                  <div className="p-12 text-center">
                    <p className="text-gray-400">No agencies registered yet.</p>
                  </div>
                )}
              </div>
            </section>

            {/* Messaging Queue */}
            <section className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden mb-6">
              <div className="p-6 border-b border-gray-800">
                <h3 className="text-xl font-bold text-white">Agency Messaging Queue</h3>
                <p className="text-gray-400 text-sm mt-1">
                  AI auto-triage with suggested responses, category detection, and priority assignment
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-950 border-b border-gray-800">
                    <tr>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Agency</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Subject</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Category</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Priority</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">AI Triaged</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Status</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {messages.map((message) => (
                      <tr key={message.id} className="border-b border-gray-800 hover:bg-gray-800 transition cursor-pointer">
                        <td className="p-4 text-white font-medium">{message.agency_name}</td>
                        <td className="p-4 text-white text-sm">{message.subject}</td>
                        <td className="p-4 text-gray-400 text-sm">{message.category}</td>
                        <td className="p-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(message.priority)}`}>
                            {message.priority}
                          </span>
                        </td>
                        <td className="p-4">
                          {message.ai_triaged ? (
                            <span className="text-purple-400 text-sm">✓ AI Triaged</span>
                          ) : (
                            <span className="text-gray-500 text-sm">—</span>
                          )}
                        </td>
                        <td className="p-4 text-gray-400 text-sm">{message.status}</td>
                        <td className="p-4 text-gray-400 text-sm">{formatDate(message.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {messages.length === 0 && (
                  <div className="p-12 text-center">
                    <p className="text-gray-400">No pending messages.</p>
                  </div>
                )}
              </div>
            </section>

            {/* Agency Analytics */}
            <section className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
              <div className="p-6 border-b border-gray-800">
                <h3 className="text-xl font-bold text-white">Agency Performance Analytics</h3>
                <p className="text-gray-400 text-sm mt-1">
                  Operational metrics with complete data isolation per agency
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-950 border-b border-gray-800">
                    <tr>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Agency</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Statements Sent</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Total Collected</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Collection Rate</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Avg Days to Payment</th>
                      <th className="text-left p-4 text-sm font-semibold text-gray-400">Active Payment Plans</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.map((agency) => (
                      <tr key={agency.agency_id} className="border-b border-gray-800">
                        <td className="p-4 text-white font-semibold">{agency.agency_name}</td>
                        <td className="p-4 text-white text-sm">{agency.total_statements_sent}</td>
                        <td className="p-4 text-white font-semibold">{formatCurrency(agency.total_collected)}</td>
                        <td className="p-4">
                          <span className={`text-sm font-semibold ${agency.collection_rate >= 80 ? 'text-green-400' : agency.collection_rate >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                            {agency.collection_rate.toFixed(1)}%
                          </span>
                        </td>
                        <td className="p-4 text-white text-sm">{agency.avg_days_to_payment}d</td>
                        <td className="p-4 text-white text-sm">{agency.active_payment_plans}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {analytics.length === 0 && (
                  <div className="p-12 text-center">
                    <p className="text-gray-400">No analytics data available.</p>
                  </div>
                )}
              </div>
            </section>
          </section>
        </div>
      </main>
    </div>
  )
}
