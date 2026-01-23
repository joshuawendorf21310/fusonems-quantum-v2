import { useAppData } from './context/useAppData.js'
import { Link } from 'react-router-dom'
import StatCard from './components/StatCard.jsx'
import SectionHeader from './components/SectionHeader.jsx'
import StatusBadge from './components/StatusBadge.jsx'
import DataTable from './components/DataTable.jsx'
import ChartPanel from './components/ChartPanel.jsx'

export default function Dashboard() {
  const { calls, units, shifts, invoices, modules } = useAppData()

  const moduleIndex = modules.reduce((acc, module) => {
    acc[module.module_key] = module
    return acc
  }, {})
  const moduleRoutes = {
    CAD: '/cad',
    COMMS: '/communications',
    EMAIL: '/email',
    EPCR: '/epcr',
    BILLING: '/billing',
    FIRE: '/fire',
    HEMS: '/hems',
    INVENTORY: '/inventory',
    NARCOTICS: '/narcotics',
    SCHEDULING: '/scheduling',
    TRAINING: '/training-center',
    QA: '/qa',
    LEGAL_PORTAL: '/legal-portal',
    TELEHEALTH: '/telehealth',
    BUILDERS: '/builders',
    FOUNDER: '/founder-ops',
  }
  const moduleSignals = [
    { key: 'CAD', label: 'CAD' },
    { key: 'COMMS', label: 'Comms' },
    { key: 'EMAIL', label: 'Email' },
    { key: 'EPCR', label: 'ePCR' },
    { key: 'BILLING', label: 'Billing' },
    { key: 'FIRE', label: 'Fire Ops' },
    { key: 'HEMS', label: 'HEMS' },
    { key: 'INVENTORY', label: 'Inventory' },
    { key: 'NARCOTICS', label: 'Narcotics' },
    { key: 'SCHEDULING', label: 'Scheduling' },
    { key: 'TRAINING', label: 'Training' },
    { key: 'QA', label: 'QA' },
    { key: 'LEGAL_PORTAL', label: 'Legal' },
    { key: 'TELEHEALTH', label: 'Telehealth' },
    { key: 'BUILDERS', label: 'Builders' },
    { key: 'FOUNDER', label: 'Monitoring' },
  ]

  const callColumns = [
    { key: 'id', label: 'Call ID' },
    { key: 'caller_name', label: 'Caller' },
    { key: 'location_address', label: 'Location' },
    {
      key: 'priority',
      label: 'Priority',
      render: (row) => <StatusBadge value={row.priority} />,
    },
    {
      key: 'status',
      label: 'Status',
      render: (row) => <StatusBadge value={row.status} />,
    },
    {
      key: 'eta_minutes',
      label: 'ETA',
      render: (row) => (row.eta_minutes ? `${row.eta_minutes} min` : 'Pending'),
    },
  ]

  const unitColumns = [
    { key: 'unit_identifier', label: 'Unit' },
    {
      key: 'status',
      label: 'Status',
      render: (row) => <StatusBadge value={row.status} />,
    },
    {
      key: 'latitude',
      label: 'Latitude',
      render: (row) => row.latitude?.toFixed?.(2) ?? row.latitude,
    },
    {
      key: 'longitude',
      label: 'Longitude',
      render: (row) => row.longitude?.toFixed?.(2) ?? row.longitude,
    },
  ]

  return (
    <div className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Live Operations Snapshot</p>
          <h2>Dispatch, clinical care, and business ops in one command view.</h2>
          <p className="hero-text">
            FusonEMS Quantum is coordinating call intake, unit response, patient
            documentation, and revenue capture across every division.
          </p>
        </div>
        <div className="hero-grid">
          <StatCard label="Active Calls" value={calls.length} delta="+6%" footnote="Last 60 min" />
          <StatCard label="Units Deployed" value={units.length} delta="+2" footnote="Across 7 zones" />
          <StatCard label="Open Shifts" value={shifts.length} delta="-1" footnote="Overtime risk" />
          <StatCard label="Invoices Pending" value={invoices.length} delta="+4" footnote="Office Ally" />
        </div>
      </section>

      <section className="section-grid">
        <div className="panel">
          <SectionHeader
            eyebrow="CAD"
            title="Priority Calls"
            action={<button className="ghost-button">Open CAD Queue</button>}
          />
          <DataTable columns={callColumns} rows={calls} emptyState="No active calls." />
        </div>
        <div className="panel">
          <SectionHeader
            eyebrow="Fleet"
            title="Unit Availability"
            action={<button className="ghost-button">View Map</button>}
          />
          <DataTable columns={unitColumns} rows={units} emptyState="No unit telemetry." />
        </div>
      </section>

      <section className="section-grid">
        <ChartPanel
          title="Call Volume Forecast"
          description="Connect CAD telemetry to enable forecasting."
          data={[]}
          emptyState="No forecast yet. Link CAD call history to activate."
        />
        <ChartPanel
          title="Revenue Capture"
          description="Awaiting billing adjudication metrics."
          data={[]}
          emptyState="No revenue trend yet. Import remittance data to activate."
        />
      </section>

      <section className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Signals" title="Module Pulse Check" />
          <div className="signal-grid">
            {moduleSignals.map((signal) => {
              const module = moduleIndex[signal.key]
              const status = module?.enabled === false ? 'Offline' : 'Active'
              const delta = module?.kill_switch ? 'Locked' : 'OK'
              const route = moduleRoutes[signal.key] || '/dashboard'
              return (
                <Link key={signal.key} to={route} className="signal-link">
                  <StatCard
                    label={signal.label}
                    value={status}
                    delta={delta}
                    footnote={module ? 'Registry linked' : 'Fallback active'}
                  />
                </Link>
              )
            })}
          </div>
        </div>
      </section>
    </div>
  )
}
