"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"

type BuilderHealth = {
  status: string
  message: string
  metrics: Record<string, number>
}

type BuildersResponse = {
  builders: {
    validation_rules: BuilderHealth
    nemsis: BuilderHealth
    exports: BuilderHealth
    email?: BuilderHealth
    spaces?: BuilderHealth
    telnyx?: BuilderHealth
    ollama?: BuilderHealth
    nemsis_dataset?: BuilderHealth
    visibility_builder?: BuilderHealth
    snomed?: BuilderHealth
    icd10?: BuilderHealth
    rxnorm?: BuilderHealth
    nemsis_state_export?: BuilderHealth
  }
  timestamp?: string
}

export function BuilderSystemsWidget() {
  const [builders, setBuilders] = useState<BuildersResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    const fetchBuilders = () => {
      apiFetch<BuildersResponse>("/api/founder/builders/health")
        .then((data) => {
          if (mounted) {
            setBuilders(data)
            setLoading(false)
          }
        })
        .catch(() => {
          if (mounted) setLoading(false)
        })
    }

    fetchBuilders()
    const interval = setInterval(fetchBuilders, 60000)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  if (loading || !builders) {
    return (
      <section className="panel">
        <header>
          <h3>Builder Systems</h3>
        </header>
        <div className="panel-card">
          <p className="muted-text">Loading builder systems...</p>
        </div>
      </section>
    )
  }

  const b = builders.builders
  return (
    <section className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
      <div className="px-6 py-5 border-b border-white/10 bg-gradient-to-r from-orange-600/10 via-transparent to-cyan-600/10">
        <h3 className="text-xl font-semibold text-white">Builder Systems</h3>
        <p className="text-zinc-400 text-sm mt-1">Validation, NEMSIS, Exports, Email, Spaces, Telnyx, Ollama, NEMSIS dataset, Visibility, SNOMED, ICD-10, RXNorm</p>
        <a
          href="/founder/terminology"
          className="inline-flex items-center gap-2 mt-3 px-4 py-2 rounded-xl bg-orange-600/20 border border-orange-500/40 text-orange-400 hover:bg-orange-600/30 hover:border-orange-500/60 text-sm font-medium transition-colors"
        >
          <span>📋</span> Terminology Builder (ICD-10, SNOMED, RXNorm)
        </a>
      </div>

      <div className="p-4 builders-grid">
        <BuilderCard
          title="Validation Rules"
          health={b.validation_rules}
          icon="📋"
          metrics={[
            { label: "Active Rules", value: b.validation_rules.metrics?.active_rules ?? "—" },
            { label: "Open Issues", value: b.validation_rules.metrics?.open_issues ?? "—" },
            { label: "High Severity", value: b.validation_rules.metrics?.high_severity_issues ?? "—" },
          ]}
        />

        <BuilderCard
          title="NEMSIS System"
          health={b.nemsis}
          icon="🏥"
          metrics={[
            { label: "Total Patients", value: b.nemsis.metrics?.total_patients ?? "—" },
            { label: "Finalized", value: b.nemsis.metrics?.finalized_patients ?? "—" },
            { label: "Avg QA Score", value: `${b.nemsis.metrics?.avg_qa_score ?? "—"}%` },
          ]}
        />

        <BuilderCard
          title="Export System"
          health={b.exports}
          icon="📤"
          metrics={[
            { label: "Total Exports", value: b.exports.metrics?.total_exports ?? "—" },
            { label: "Pending", value: b.exports.metrics?.pending_exports ?? "—" },
            { label: "Failure Rate", value: `${b.exports.metrics?.failure_rate_pct ?? "—"}%` },
          ]}
        />

        {b.email && (
          <BuilderCard
            title="Email (SMTP/IMAP)"
            health={b.email}
            icon="✉️"
            metrics={[
              { label: "SMTP", value: b.email.metrics?.smtp_configured ? "Configured" : "Not set" },
              { label: "IMAP", value: b.email.metrics?.imap_configured ? "Configured" : "Not set" },
            ]}
          />
        )}

        {b.spaces && (
          <BuilderCard
            title="Spaces (Documents)"
            health={b.spaces}
            icon="📦"
            metrics={[
              { label: "Spaces", value: b.spaces.metrics?.configured ? "Configured" : "Not set" },
            ]}
          />
        )}

        {b.telnyx && (
          <BuilderCard
            title="Telnyx (IVR/Phone)"
            health={b.telnyx}
            icon="📞"
            metrics={[
              { label: "Enabled", value: b.telnyx.metrics?.enabled ? "Yes" : "No" },
              { label: "Configured", value: b.telnyx.metrics?.configured ? "Yes" : "No" },
            ]}
          />
        )}

        {b.ollama && (
          <BuilderCard
            title="Ollama (AI)"
            health={b.ollama}
            icon="🤖"
            metrics={[
              { label: "Enabled", value: b.ollama.metrics?.enabled ? "Yes" : "No" },
              { label: "URL set", value: b.ollama.metrics?.url_configured ? "Yes" : "No" },
            ]}
          />
        )}

        {b.nemsis_dataset && (
          <BuilderCard
            title="NEMSIS Dataset"
            health={b.nemsis_dataset}
            icon="📋"
            metrics={[
              { label: "Elements", value: b.nemsis_dataset.metrics?.elements_defined ?? "—" },
            ]}
          />
        )}

        {b.visibility_builder && (
          <BuilderCard
            title="Visibility Builder"
            health={b.visibility_builder}
            icon="👁"
            metrics={[
              { label: "Active rules", value: b.visibility_builder.metrics?.active_rules ?? "—" },
              { label: "Total rules", value: b.visibility_builder.metrics?.total_rules ?? "—" },
            ]}
          />
        )}

        {b.snomed && (
          <BuilderCard
            title="SNOMED"
            health={b.snomed}
            icon="🏷"
            metrics={[
              { label: "Loaded", value: b.snomed.metrics?.loaded ? "Yes" : "No" },
            ]}
          />
        )}

        {b.icd10 && (
          <BuilderCard
            title="ICD-10"
            health={b.icd10}
            icon="📑"
            metrics={[
              { label: "Full dataset", value: b.icd10.metrics?.full_dataset ? "Yes" : "Heuristics only" },
            ]}
          />
        )}

        {b.rxnorm && (
          <BuilderCard
            title="RXNorm"
            health={b.rxnorm}
            icon="💊"
            metrics={[
              { label: "Loaded", value: b.rxnorm.metrics?.loaded ? "Yes" : "No" },
            ]}
          />
        )}

        {b.nemsis_state_export && (
          <BuilderCard
            title="NEMSIS / State Export"
            health={b.nemsis_state_export}
            icon="📤"
            metrics={[
              { label: "Export on finalize", value: b.nemsis_state_export.metrics?.export_on_finalize ? "Yes" : "No" },
              { label: "State endpoints", value: b.nemsis_state_export.metrics?.state_configured ? "Configured" : "Not set" },
            ]}
          />
        )}
      </div>

      <style jsx>{`
        .builders-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 1.25rem;
        }
      `}</style>
    </section>
  )
}

function BuilderCard({
  title,
  health,
  icon,
  metrics,
}: {
  title: string
  health: BuilderHealth
  icon: string
  metrics: { label: string; value: string | number }[]
}) {
  const statusColor = {
    HEALTHY: "success",
    WARNING: "warning",
    DEGRADED: "warning",
    CRITICAL: "error",
    UNKNOWN: "muted",
  }[health.status] || "muted"

  const borderClass =
    statusColor === "success"
      ? "border-l-emerald-500/60"
      : statusColor === "warning"
      ? "border-l-amber-500/60"
      : statusColor === "error"
      ? "border-l-red-500/60"
      : "border-l-zinc-600/60"

  return (
    <article className={`platform-card ${statusColor} rounded-xl border border-white/10 bg-zinc-900/40 overflow-hidden border-l-4 ${borderClass}`}>
      <div className="builder-header">
        <span className="builder-icon">{icon}</span>
        <div>
          <strong>{title}</strong>
          <p className="muted-text">{health.status}</p>
        </div>
      </div>

      <p className="builder-message">{health.message}</p>

      <div className="builder-metrics">
        {metrics.map((metric) => (
          <div key={metric.label} className="metric">
            <span className="metric-label">{metric.label}</span>
            <span className="metric-value">{metric.value}</span>
          </div>
        ))}
      </div>

      <style jsx>{`
        .builder-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.75rem;
        }
        .builder-icon {
          font-size: 2rem;
        }
        .builder-message {
          font-size: 0.85rem;
          color: #666;
          margin: 0 0 1rem 0;
        }
        .builder-metrics {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .metric {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem;
          background: rgba(0, 0, 0, 0.02);
          border-radius: 8px;
        }
        .metric-label {
          font-size: 0.85rem;
          color: #666;
        }
        .metric-value {
          font-weight: 600;
          font-size: 0.9rem;
        }
      `}</style>
    </article>
  )
}
