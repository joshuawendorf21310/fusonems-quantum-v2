import StatCard from '../components/StatCard.jsx'
import SectionHeader from '../components/SectionHeader.jsx'
import { fallbackFounderKpis } from '../data/fallback.js'

export default function FounderDashboard() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Founder Console"
        title="Enterprise Command & Strategic Controls"
        action={<button className="ghost-button">Board Packet</button>}
      />

      <div className="grid-3">
        {fallbackFounderKpis.map((kpi) => (
          <StatCard key={kpi.label} label={kpi.label} value={kpi.value} delta={kpi.delta} />
        ))}
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Ops" title="Multi-Agency Performance" />
          <ul className="checklist">
            <li>24 agencies connected through shared CAD rules.</li>
            <li>Median ETA down 14% after AI staging rollout.</li>
            <li>Fleet downtime reduced to 2.1% this quarter.</li>
          </ul>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Security" title="Governance" />
          <ul className="checklist">
            <li>RBAC enforced across 5 business units.</li>
            <li>Data retention policies aligned with state mandates.</li>
            <li>Encryption at rest verified for all clinical data.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
