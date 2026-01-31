"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"

import Sidebar from "@/components/layout/Sidebar"
import Topbar from "@/components/layout/Topbar"
import {
  SystemHealthWidget,
  StorageQuotaWidget,
  RecentActivityWidget,
  BuilderSystemsWidget,
  FailedOperationsWidget,
  CommunicationDashboard,
  AIBillingWidget,
  EPCRImportWidget,
  AccountingDashboardWidget,
  ExpensesDashboardWidget,
  MarketingAnalyticsWidget,
  ReportingDashboardWidget,
  ProtocolsDashboardWidget
} from "@/components/founder"
import FounderAIChat from "@/components/founder/FounderAIChat"
import FounderScreenShare from "@/components/founder/FounderScreenShare"
import { apiFetch } from "@/lib/api"
import { PageShell } from "@/components/PageShell"

type ModuleHealth = {
  module_key: string
  health_state: string
  enabled: boolean
  kill_switch: boolean
  degraded: boolean
}

type FounderOverview = {
  orgs: { id: number; name: string; status: string; lifecycle_state: string }[]
  module_health: ModuleHealth[]
  active_degradation: boolean
  queue_summary: { total: number; queued: number; errors: number; error_rate: number }
  critical_audits: { id: number; actor_email: string; action: string; resource: string; created_at: string | null }[]
}

export default function FounderPage() {
  const [overview, setOverview] = useState<FounderOverview | null>(null)
  const [error, setError] = useState<string>("")

  useEffect(() => {
    let mounted = true
    apiFetch<FounderOverview>("/api/founder/overview")
      .then((data) => {
        if (mounted) {
          setOverview(data)
        }
      })
      .catch(() => {
        if (mounted) {
          setError("Unable to load founder overview")
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  const queueItems = useMemo(() => {
    if (!overview) return []
    return [
      { label: "Queue depth", value: overview.queue_summary.total },
      { label: "Pending jobs", value: overview.queue_summary.queued },
      { label: "Error rate", value: `${(overview.queue_summary.error_rate * 100).toFixed(1)}%` },
      { label: "Active errors", value: overview.queue_summary.errors },
    ]
  }, [overview])

  const [activeTab, setActiveTab] = useState('overview');
  return (
    <PageShell title="Founder Console" requireAuth={true} allowedRoles={["founder"]}>
      <Sidebar />
      <main className="ml-64">
        <Topbar />
        <div className="p-8 max-w-7xl mx-auto">
          <nav className="flex gap-2 mb-8">
            <button
              onClick={() => setActiveTab("overview")}
              className={`py-2.5 px-5 rounded-xl font-medium transition-all ${
                activeTab === "overview"
                  ? "bg-gradient-to-r from-orange-600 to-orange-500 text-white shadow-lg shadow-orange-500/20"
                  : "bg-zinc-800/80 text-zinc-400 hover:text-white hover:bg-zinc-700"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab("ai-chat")}
              className={`py-2.5 px-5 rounded-xl font-medium transition-all ${
                activeTab === "ai-chat"
                  ? "bg-gradient-to-r from-orange-600 to-orange-500 text-white shadow-lg shadow-orange-500/20"
                  : "bg-zinc-800/80 text-zinc-400 hover:text-white hover:bg-zinc-700"
              }`}
            >
              ✨ AI Chat
            </button>
            <button
              onClick={() => setActiveTab("screen-share")}
              className={`py-2.5 px-5 rounded-xl font-medium transition-all ${
                activeTab === "screen-share"
                  ? "bg-gradient-to-r from-orange-600 to-orange-500 text-white shadow-lg shadow-orange-500/20"
                  : "bg-zinc-800/80 text-zinc-400 hover:text-white hover:bg-zinc-700"
              }`}
            >
              Screen Share
            </button>
          </nav>
          {activeTab === "overview" && (
            <section className="space-y-8">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4 flex flex-wrap gap-3">
                <p className="text-white/70 text-sm w-full">So what? — Next actions</p>
                <Link href="/billing/dashboard" className="px-4 py-2 rounded-lg bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 transition text-sm">Billing dashboard</Link>
                <Link href="/compliance/baa" className="px-4 py-2 rounded-lg bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 transition text-sm">BAA status</Link>
                <Link href="/billing" className="px-4 py-2 rounded-lg bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 transition text-sm">Claims & submit</Link>
                <Link href="/founder/terminology" className="px-4 py-2 rounded-lg bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 transition text-sm">Terminology builder</Link>
                <Link href="/epcr" className="px-4 py-2 rounded-lg bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 transition text-sm">ePCR & NEMSIS</Link>
              </div>
              <header className="relative rounded-2xl overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-orange-600/15 via-transparent to-cyan-600/10" />
                <div className="relative px-8 py-8">
                  <p className="text-orange-400 text-sm font-medium uppercase tracking-wider">Founder Console</p>
                  <h2 className="text-3xl font-bold text-white mt-1">Command-grade overview</h2>
                  {error ? (
                    <p className="text-zinc-400 mt-2">{error}</p>
                  ) : (
                    <p className="text-zinc-400 mt-2 text-lg">
                      Real-time system health, storage, builders, and operational intelligence.
                    </p>
                  )}
                </div>
              </header>
              {/* At a glance */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <article className="rounded-xl border border-white/10 bg-white/5 p-5">
                  <p className="text-zinc-500 text-sm">Queue depth</p>
                  <p className="text-2xl font-bold text-white mt-1">{overview?.queue_summary?.total ?? "—"}</p>
                </article>
                <article className="rounded-xl border border-white/10 bg-white/5 p-5">
                  <p className="text-zinc-500 text-sm">Pending jobs</p>
                  <p className="text-2xl font-bold text-white mt-1">{overview?.queue_summary?.queued ?? "—"}</p>
                </article>
                <article className="rounded-xl border border-white/10 bg-white/5 p-5">
                  <p className="text-zinc-500 text-sm">Organizations</p>
                  <p className="text-2xl font-bold text-white mt-1">{overview?.orgs?.length ?? 0}</p>
                </article>
                <article className={`rounded-xl border p-5 ${overview?.active_degradation ? "border-amber-500/50 bg-amber-500/10" : "border-white/10 bg-white/5"}`}>
                  <p className="text-zinc-500 text-sm">Active degradation</p>
                  <p className={`text-2xl font-bold mt-1 ${overview?.active_degradation ? "text-amber-400" : "text-white"}`}>
                    {overview?.active_degradation ? "Yes" : "No"}
                  </p>
                </article>
              </div>
              <SystemHealthWidget />
              <CommunicationDashboard />
              <AIBillingWidget />
              <EPCRImportWidget />
              <AccountingDashboardWidget />
              <ExpensesDashboardWidget />
              <MarketingAnalyticsWidget />
              <ReportingDashboardWidget />
              <div className="platform-card-grid">
                <StorageQuotaWidget />
                {queueItems.map((item) => (
                  <article key={item.label} className="platform-card">
                    <p className="muted-text">{item.label}</p>
                    <strong>{item.value}</strong>
                  </article>
                ))}
                <article
                  className={`platform-card ${overview?.active_degradation ? "warning" : ""}`}
                >
                  <p className="muted-text">Active degradation</p>
                  <strong>{overview?.active_degradation ? "Yes" : "No"}</strong>
                </article>
              </div>
              <BuilderSystemsWidget />
              <FailedOperationsWidget />
              <RecentActivityWidget />
              <div className="data-grid">
                <section className="panel">
                  <header>
                    <h3>Organizations</h3>
                  </header>
                  <div className="panel-stack">
                    {(overview?.orgs ?? []).map((org) => (
                      <article key={org.id} className="panel-card">
                        <div>
                          <strong>{org.name}</strong>
                          <p className="muted-text">
                            {org.lifecycle_state} • {org.status}
                          </p>
                        </div>
                        <Link className="cta-button cta-secondary" href={`/founder/orgs/${org.id}`}>
                          View org
                        </Link>
                      </article>
                    ))}
                    {!overview && <p className="muted-text">Loading orgs...</p>}
                  </div>
                </section>
                <section className="panel">
                  <header>
                    <h3>Module health</h3>
                  </header>
                  <div className="panel-stack">
                    {overview?.module_health.map((module) => (
                      <article
                        key={module.module_key}
                        className={`panel-card ${module.degraded ? "warning" : ""}`}
                      >
                        <div>
                          <strong>{module.module_key}</strong>
                          <p className="muted-text">
                            {module.health_state} • {module.enabled ? "Enabled" : "Disabled"}
                          </p>
                        </div>
                        {module.kill_switch && <span className="status-pill">Kill switch</span>}
                      </article>
                    ))}
                    {!overview && <p className="muted-text">Loading modules...</p>}
                  </div>
                </section>
              </div>
              <section className="panel">
                <header>
                  <h3>Critical audits</h3>
                  <p className="muted-text">Top entries include auth, billing, merge, and lock operations.</p>
                </header>
                <ul className="audit-list">
                  {(overview?.critical_audits ?? []).slice(0, 6).map((audit) => (
                    <li key={audit.id}>
                      <strong>{audit.action}</strong>
                      <p className="muted-text">
                        {audit.resource} • {audit.actor_email} • {audit.created_at ?? "?"}
                      </p>
                    </li>
                  ))}
                  {!overview && <li className="muted-text">Loading audits...</li>}
                </ul>
              </section>
            </section>
          )}
          {activeTab === "ai-chat" && (
            <section>
              <FounderAIChat />
            </section>
          )}
          {activeTab === "screen-share" && (
            <section>
              <FounderScreenShare />
            </section>
          )}
        </div>
      </main>
    </PageShell>
  )
}
