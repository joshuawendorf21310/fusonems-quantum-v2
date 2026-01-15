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
        {fallbackInvestorKpis.map((kpi) => (
          <StatCard key={kpi.label} label={kpi.label} value={kpi.value} delta={kpi.delta} />
        ))}
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Highlights" title="Momentum" />
        <ul className="checklist">
          <li>Pipeline: 12 enterprise agencies in contracting.</li>
          <li>Net retention: 118% with upsell to AI analytics.</li>
          <li>Unit tracking utilization: 91% across live deployments.</li>
        </ul>
      </div>
    </div>
  )
}
