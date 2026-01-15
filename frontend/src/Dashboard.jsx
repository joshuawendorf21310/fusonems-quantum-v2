import { useAppData } from './context/AppContext.jsx'
import StatCard from './components/StatCard.jsx'
import SectionHeader from './components/SectionHeader.jsx'
import StatusBadge from './components/StatusBadge.jsx'
import DataTable from './components/DataTable.jsx'
import ChartPanel from './components/ChartPanel.jsx'

export default function Dashboard() {
  const { calls, units, shifts, invoices } = useAppData()

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
          description="Projected calls per hour for the next 8 hours."
          data={[6, 5, 9, 12, 8, 4, 6, 5]}
        />
        <ChartPanel
          title="Revenue Capture"
          description="Claims processing velocity versus last week."
          data={[4, 6, 7, 6, 9, 11, 8, 10]}
        />
      </section>
    </div>
  )
}
