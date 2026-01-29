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
import { apiFetch } from "@/lib/api"

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

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Sidebar />
      <main className="ml-64">
        <Topbar />
        <div className="p-6">
          <section className="space-y-6">
            <header>
              <p className="eyebrow">Founder Console</p>
              <h2>Command-grade overview</h2>
              {error ? (
                <p className="muted-text">{error}</p>
              ) : (
                <p className="muted-text">
                  Real-time system health, storage, builders, and operational intelligence.
                </p>
              )}
            </header>

            {/* System Health - Top Priority */}
            <SystemHealthWidget />

            {/* Communication System - Unified communication platform */}
            <CommunicationDashboard />

            {/* AI Billing Assistant - For Single Biller Workflow */}
            <AIBillingWidget />

            {/* ePCR Import - ImageTrend/ZOLL Integration */}
            <EPCRImportWidget />

            {/* Accounting Dashboard - Cash/AR/P&L/Tax */}
            <AccountingDashboardWidget />

            {/* Receipts & Expenses - OCR & Approval Workflows */}
            <ExpensesDashboardWidget />

            {/* Marketing Analytics - Demo Requests & Lead Generation */}
            <MarketingAnalyticsWidget />

            {/* Reporting & Analytics - System-wide Reports & Compliance */}
            <ReportingDashboardWidget />

            {/* Protocols Management - Import, Review, Tag, Search */}
            <ProtocolsDashboardWidget />

            {/* Critical Metrics Grid */}
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

            {/* Builder Systems Health */}
            <BuilderSystemsWidget />

            {/* Failed Operations Alert */}
            <FailedOperationsWidget />

            {/* Recent Activity */}
            <RecentActivityWidget />

            {/* Organizations and Modules */}
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

            {/* Critical Audits */}
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
        </div>
      </main>
    </div>
  )
}
