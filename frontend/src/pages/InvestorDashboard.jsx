import StatCard from '../components/StatCard.jsx'
import SectionHeader from '../components/SectionHeader.jsx'
import { fallbackInvestorKpis } from '../data/fallback.js'

export default function InvestorDashboard() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Investor View"
        title="Growth, Margin, and Expansion Metrics"
        action={<button className="ghost-button">Download One-Pager</button>}
      />

      <div className="grid-3">
        {fallbackInvestorKpis.length > 0 ? (
          fallbackInvestorKpis.map((kpi) => (
            <StatCard key={kpi.label} label={kpi.label} value={kpi.value} delta={kpi.delta} />
          ))
        ) : (
          <div className="panel note-stack">
            <p className="eyebrow">Investor KPIs</p>
            <h3>Connect live revenue and utilization feeds.</h3>
            <p className="note-body">
              Investor metrics populate after billing, scheduling, and operations telemetry are linked.
            </p>
          </div>
        )}
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Highlights" title="Momentum" />
        <ul className="checklist">
          <li>Upload board materials for automated investor reporting.</li>
          <li>Enable revenue telemetry to show retention and margin trends.</li>
          <li>Connect fleet utilization feeds for operational visibility.</li>
        </ul>
      </div>
    </div>
  )
}
