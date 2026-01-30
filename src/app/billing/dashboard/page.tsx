"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { apiFetch } from "@/lib/api"
import ClaimCard from "@/components/billing/ClaimCard"
import DenialRiskBadge from "@/components/billing/DenialRiskBadge"
import FacesheetStatus from "@/components/billing/FacesheetStatus"
import AIAssistPanel from "@/components/billing/AIAssistPanel"
import OfficeAllyTracker from "@/components/billing/OfficeAllyTracker"

type ConsoleSummary = {
  counts: {
    pending: number
    ready: number
    submitted: number
    denied: number
    paid_mtd: number
  }
  facesheet_gaps: number
  ai_insights: { id: number; type: string; description: string; created_at?: string }[]
}

type ClaimReady = {
  id: number
  payer: string
  status: string
  denial_risks: string[]
  office_ally_batch_id?: string
  created_at?: string
}

type CallQueueEntry = {
  id: number
  intent: string
  resolution: string
  created_at?: string
}

type SpeedMetrics = {
  avg_hours_claim_to_submitted: number
  min_hours_claim_to_submitted: number
  max_hours_claim_to_submitted: number
  first_pass_rate: number
  submitted_mtd: number
  pending_count: number
}

export default function BillingDashboard() {
  const [summary, setSummary] = useState<ConsoleSummary | null>(null)
  const [readyClaims, setReadyClaims] = useState<ClaimReady[]>([])
  const [callQueue, setCallQueue] = useState<CallQueueEntry[]>([])
  const [speed, setSpeed] = useState<SpeedMetrics | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchSummary()
    fetchReadyClaims()
    fetchCallQueue()
    fetchSpeed()
  }, [])

  const fetchSpeed = async () => {
    try {
      const data = await apiFetch<SpeedMetrics>("/billing/console/speed")
      setSpeed(data)
    } catch (error) {
      console.error(error)
    }
  }

  const fetchSummary = async () => {
    setLoading(true)
    try {
      const data = await apiFetch<ConsoleSummary>("/billing/console/summary")
      setSummary(data)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const fetchReadyClaims = async () => {
    try {
      const data = await apiFetch<ClaimReady[]>("/billing/console/claims-ready")
      setReadyClaims(data)
    } catch (error) {
      console.error(error)
    }
  }

  const fetchCallQueue = async () => {
    try {
      const data = await apiFetch<CallQueueEntry[]>("/billing/console/call-queue")
      setCallQueue(data)
    } catch (error) {
      console.error(error)
    }
  }

  const cards = [
    { label: "Pending", value: summary?.counts.pending ?? 0 },
    { label: "Ready", value: summary?.counts.ready ?? 0 },
    { label: "Submitted", value: summary?.counts.submitted ?? 0 },
    { label: "Denied", value: summary?.counts.denied ?? 0 },
    { label: "Paid (MTD)", value: summary?.counts.paid_mtd ?? 0 },
  ]

  return (
    <main className="page-shell" style={{ minHeight: "100vh" }}>
      <div className="page-container">
        <section className="glass-panel" style={{ padding: "2rem" }}>
          <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <p className="section-title" style={{ margin: 0 }}>Billing Dashboard</p>
              <p className="section-subtitle">Live status for claims, AI, facesheets, and calls.</p>
              <p style={{ margin: "0.35rem 0 0", fontSize: "0.85rem", color: "rgba(255,124,41,0.9)" }}>
                You&apos;re the only biller—AI does as much as possible. One queue, no round-robin.
              </p>
            </div>
            <button
              type="button"
              onClick={() => { fetchSummary(); fetchSpeed(); }}
              style={{
                borderRadius: 8,
                border: "1px solid rgba(255,255,255,0.3)",
                background: "transparent",
                color: "#f7f6f3",
                padding: "0.4rem 1rem",
                cursor: "pointer",
              }}
            >
              Refresh
            </button>
          </header>
          {speed != null && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                gap: "1rem",
                marginTop: "1.25rem",
                padding: "1rem",
                borderRadius: 12,
                background: "rgba(12,12,12,0.8)",
                border: "1px solid rgba(255,124,41,0.2)",
              }}
            >
              <div>
                <p style={{ margin: 0, color: "#bbb", fontSize: "0.8rem" }}>Avg claim → submitted</p>
                <strong style={{ fontSize: "1.2rem", color: "var(--accent-orange)" }}>{speed.avg_hours_claim_to_submitted}h</strong>
              </div>
              <div>
                <p style={{ margin: 0, color: "#bbb", fontSize: "0.8rem" }}>First-pass rate</p>
                <strong style={{ fontSize: "1.2rem", color: "var(--success)" }}>{(speed.first_pass_rate * 100).toFixed(0)}%</strong>
              </div>
              <div>
                <p style={{ margin: 0, color: "#bbb", fontSize: "0.8rem" }}>Submitted (MTD)</p>
                <strong style={{ fontSize: "1.2rem", color: "#f7f6f3" }}>{speed.submitted_mtd}</strong>
              </div>
              <div>
                <p style={{ margin: 0, color: "#bbb", fontSize: "0.8rem" }}>Pending</p>
                <strong style={{ fontSize: "1.2rem", color: "#f7f6f3" }}>{speed.pending_count}</strong>
              </div>
            </div>
          )}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
              gap: "1rem",
              marginTop: "1.5rem",
            }}
          >
            {cards.map((card) => (
              <div
                key={card.label}
                style={{
                  padding: "1rem",
                  borderRadius: 12,
                  background: "rgba(12,12,12,0.7)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
              >
                <p style={{ margin: 0, color: "#bbb" }}>{card.label}</p>
                <strong style={{ fontSize: "1.6rem", color: "#ff7c29" }}>{card.value}</strong>
              </div>
            ))}
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1rem",
              marginTop: "1.5rem",
            }}
          >
            <FacesheetStatus
              present={!summary || summary.facesheet_gaps === 0}
              missingFields={!summary || summary.facesheet_gaps > 0 ? ["demographics"] : []}
            />
            <OfficeAllyTracker status={summary ? "monitoring" : "idle"} />
            <AIAssistPanel
              cards={summary?.ai_insights.map((insight) => ({
                title: insight.type.replace("_", " "),
                summary: insight.description || "AI insight available",
                footer: insight.created_at ? new Date(insight.created_at).toLocaleString() : undefined,
              }))}
            />
          </div>
        </section>
        <section className="glass-panel" style={{ marginTop: "1.5rem", padding: "2rem" }}>
          <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <p className="section-title" style={{ margin: 0 }}>Claims Ready to Submit</p>
              <p style={{ margin: 0, color: "#bbb", fontSize: "0.9rem" }}>
                One click submit uses Office Ally export endpoint.
              </p>
            </div>
            <Link href="/billing/claims-ready" className="cta-button cta-secondary">
              Full view
            </Link>
          </header>
          <div
            style={{
              display: "grid",
              gap: "1rem",
              marginTop: "1.2rem",
            }}
          >
            {readyClaims.map((claim) => (
              <ClaimCard
                key={claim.id}
                id={claim.id}
                payer={claim.payer}
                status={claim.status}
                denialRisks={claim.denial_risks}
                createdAt={claim.created_at}
                officeAllyBatch={claim.office_ally_batch_id}
                onSubmit={() => {
                  fetch(`/api/billing/claims/${claim.id}/export/office_ally`, { method: "GET" })
                  fetchSummary()
                }}
              />
            ))}
            {!readyClaims.length && <p style={{ color: "#bbb" }}>No ready claims today.</p>}
          </div>
        </section>
        <section className="glass-panel" style={{ marginTop: "1.5rem", padding: "2rem" }}>
          <header>
            <p className="section-title" style={{ margin: 0 }}>Call Queue</p>
          </header>
          <div style={{ marginTop: "1rem" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "0.5rem", color: "#bbb" }}>ID</th>
                  <th style={{ textAlign: "left", padding: "0.5rem", color: "#bbb" }}>Intent</th>
                  <th style={{ textAlign: "left", padding: "0.5rem", color: "#bbb" }}>Resolution</th>
                  <th style={{ textAlign: "left", padding: "0.5rem", color: "#bbb" }}>Received</th>
                </tr>
              </thead>
              <tbody>
                {callQueue.map((entry) => (
                  <tr key={entry.id} style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                    <td style={{ padding: "0.65rem", color: "#f7f6f3" }}>{entry.id}</td>
                    <td style={{ padding: "0.65rem", color: "#f7f6f3" }}>{entry.intent}</td>
                    <td style={{ padding: "0.65rem", color: "#f7f6f3" }}>{entry.resolution || "pending"}</td>
                    <td style={{ padding: "0.65rem", color: "#f7f6f3" }}>{entry.created_at ? new Date(entry.created_at).toLocaleTimeString() : "n/a"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!callQueue.length && <p style={{ color: "#bbb", marginTop: "1rem" }}>No active calls.</p>}
          </div>
        </section>
      </div>
    </main>
  )
}
