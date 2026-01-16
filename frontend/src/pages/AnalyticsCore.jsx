import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import StatCard from '../components/StatCard.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackMetrics, fallbackUsageEvents } from '../data/fallback.js'

const usageColumns = [
  { key: 'event_key', label: 'Event' },
  { key: 'module_key', label: 'Module' },
  { key: 'classification', label: 'Class' },
  { key: 'created_at', label: 'Timestamp' },
]

export default function AnalyticsCore() {
  const [metrics, setMetrics] = useState(fallbackMetrics)
  const [usage, setUsage] = useState(fallbackUsageEvents)

  const loadMetrics = async () => {
    try {
      const data = await apiFetch('/api/analytics/metrics')
      if (Array.isArray(data) && data.length > 0) {
        setMetrics(data)
      }
    } catch (error) {
      console.warn('Metrics unavailable', error)
    }
  }

  const loadUsage = async () => {
    try {
      const data = await apiFetch('/api/analytics/usage')
      if (Array.isArray(data) && data.length > 0) {
        setUsage(data)
      }
    } catch (error) {
      console.warn('Usage events unavailable', error)
    }
  }

  useEffect(() => {
    loadMetrics()
    loadUsage()
  }, [])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Analytics Core"
        title="Operational Intelligence Backbone"
        action={<button className="primary-button">Generate Forecast</button>}
      />

      <div className="stat-grid">
        {metrics.length > 0 ? (
          metrics.slice(0, 3).map((metric) => (
            <StatCard
              key={metric.id}
              label={metric.metric_key}
              value={metric.metric_value}
              delta={metric.window}
              footnote={metric.tags?.module || metric.tags?.scope || 'rolling'}
            />
          ))
        ) : (
          <div className="panel note-stack">
            <p className="eyebrow">Metrics</p>
            <h3>Metrics appear once telemetry streams are connected.</h3>
            <p className="note-body">
              Enable analytics ingestion for CAD, billing, and staffing to populate KPIs.
            </p>
          </div>
        )}
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Usage" title="Event Telemetry" />
          <DataTable columns={usageColumns} rows={usage} emptyState="No usage events yet." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Predictive Lens"
            model="forecast-engine"
            version="0.9"
            level="ADVISORY"
            message="Forecasts will appear after usage telemetry and staffing inputs are available."
            reason="Historical + system utilization"
          />
          <div className="note-card">
            <p className="note-title">Latency Watch</p>
            <p className="note-body">Latency metrics will populate after monitoring is enabled.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
