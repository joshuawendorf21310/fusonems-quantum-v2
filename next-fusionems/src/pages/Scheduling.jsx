import { useAppData } from '../context/useAppData.js'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

export default function Scheduling() {
  const { shifts } = useAppData()

  const columns = [
    { key: 'crew_name', label: 'Crew' },
    {
      key: 'shift_start',
      label: 'Start',
      render: (row) => new Date(row.shift_start).toLocaleString(),
    },
    {
      key: 'shift_end',
      label: 'End',
      render: (row) => new Date(row.shift_end).toLocaleString(),
    },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
    {
      key: 'certifications',
      label: 'Certifications',
      render: (row) => row.certifications?.join(', ') || 'None',
    },
  ]

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Scheduling"
        title="Shift Coverage & Staffing"
        action={<button className="ghost-button">Open Calendar</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <DataTable columns={columns} rows={shifts} emptyState="No scheduled shifts." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Alerts" title="Coverage Risks" />
          <div className="stack">
            <div className="list-row">
              <div>
                <p className="list-title">Night ALS 1</p>
                <p className="list-sub">Overtime threshold in 2 hours</p>
              </div>
              <StatusBadge value="High" />
            </div>
            <div className="list-row">
              <div>
                <p className="list-title">Zone 7 BLS</p>
                <p className="list-sub">Need EMT coverage for 18:00-22:00</p>
              </div>
              <StatusBadge value="Routine" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
