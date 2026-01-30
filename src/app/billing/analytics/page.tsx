"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"
import RCMChart from "@/components/billing/RCMChart"

type AnalyticsPayload = {
  denial_rate: number
  aging: Record<string, number>
  payer_mix: { payer: string; count: number }[]
  days_to_pay: number
  paid_month_to_date: number
}

export default function BillingAnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null)

  useEffect(() => {
    apiFetch<AnalyticsPayload>("/billing/console/analytics")
      .then(setAnalytics)
      .catch(console.error)
  }, [])

  if (!analytics) {
    return <p className="page-shell">Loading analytics…</p>
  }

  return (
    <main className="page-shell">
      <section className="glass-panel" style={{ padding: "2rem" }}>
        <header>
          <p className="section-title" style={{ margin: 0 }}>Analytics & RCM</p>
          <p style={{ margin: 0, color: "#bbb" }}>Denial rates, aging, payer mix, and cash velocity.</p>
        </header>
        <div style={{ marginTop: "1.5rem", display: "grid", gap: "1rem" }}>
          <div
            style={{
              background: "rgba(12,12,12,0.8)",
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.08)",
              padding: "1rem",
            }}
          >
            <p style={{ margin: 0, color: "#bbb" }}>Denial Rate</p>
            <strong style={{ fontSize: "2rem", color: "#ff7c29" }}>{(analytics.denial_rate * 100).toFixed(1)}%</strong>
          </div>
          <div
            style={{
              background: "rgba(12,12,12,0.8)",
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.08)",
              padding: "1rem",
            }}
          >
            <p style={{ margin: 0, color: "#bbb" }}>Days to Pay (avg)</p>
            <strong style={{ fontSize: "2rem", color: "#ff7c29" }}>{analytics.days_to_pay.toFixed(1)}</strong>
          </div>
          <div
            style={{
              background: "rgba(12,12,12,0.8)",
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.08)",
              padding: "1rem",
            }}
          >
            <p style={{ margin: 0, color: "#bbb" }}>Paid (MTD)</p>
            <strong style={{ fontSize: "2rem", color: "#ff7c29" }}>{analytics.paid_month_to_date}</strong>
          </div>
        </div>
        <div style={{ marginTop: "1.5rem", display: "grid", gap: "1.2rem", minWidth: 320, minHeight: 160 }}>
          <RCMChart
            title="Aging (days)"
            data={Object.entries(analytics.aging).map(([bucket, value]) => ({ label: `${bucket}+`, value }))}
          />
          <RCMChart
            title="Top Payers"
            data={analytics.payer_mix.map((entry) => ({ label: entry.payer, value: entry.count }))}
          />
        </div>
      </section>
    </main>
  )
}
