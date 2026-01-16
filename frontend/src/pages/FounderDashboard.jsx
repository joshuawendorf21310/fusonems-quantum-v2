import StatCard from '../components/StatCard.jsx'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { useAppData } from '../context/useAppData.js'
import { fallbackFounderKpis } from '../data/fallback.js'

export default function FounderDashboard() {
  const { modules, systemHealth } = useAppData()
  const moduleColumns = [
    { key: 'module_key', label: 'Module' },
    { key: 'health_state', label: 'Health' },
    { key: 'enabled', label: 'Enabled' },
    { key: 'kill_switch', label: 'Kill Switch' },
  ]
  const moduleRows = modules.map((module) => ({
    module_key: module.module_key,
    health_state: module.health_state || 'UNKNOWN',
    enabled: module.enabled ? 'Yes' : 'No',
    kill_switch: module.kill_switch ? 'On' : 'Off',
  }))
  const upgradeStatus = systemHealth?.upgrade?.status || 'UNKNOWN'

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Founder Console"
        title="Enterprise Command & Strategic Controls"
        action={<button className="ghost-button">Board Packet</button>}
      />

      <div className="grid-3">
        {fallbackFounderKpis.length > 0 ? (
          fallbackFounderKpis.map((kpi) => (
            <StatCard key={kpi.label} label={kpi.label} value={kpi.value} delta={kpi.delta} />
          ))
        ) : (
          <div className="panel note-stack">
            <p className="eyebrow">Founder KPIs</p>
            <h3>Connect revenue, usage, and compliance feeds.</h3>
            <p className="note-body">
              Once billing exports, system health, and usage telemetry are live, KPIs will appear here.
            </p>
          </div>
        )}
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Ops" title="Multi-Agency Performance" />
          <ul className="checklist">
            <li>Link CAD throughput metrics to populate performance deltas.</li>
            <li>Enable fleet telemetry to surface readiness and uptime trends.</li>
            <li>Connect staffing data to show coverage risk and fatigue signals.</li>
          </ul>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Security" title="Governance" />
          <ul className="checklist">
            <li>Verify RBAC policy mappings per agency.</li>
            <li>Confirm retention policy targets for legal and clinical records.</li>
            <li>Run encryption checks to confirm data-at-rest posture.</li>
          </ul>
        </div>
      </div>

      <div className="panel">
        <SectionHeader
          eyebrow="System Health"
          title={`Upgrade Readiness: ${upgradeStatus}`}
          action={<button className="ghost-button">Open Health Center</button>}
        />
        <DataTable
          columns={moduleColumns}
          rows={moduleRows}
          emptyState="Module registry not available yet."
        />
      </div>
    </div>
  )
}
