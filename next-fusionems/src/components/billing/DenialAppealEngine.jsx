import SectionHeader from '../SectionHeader.jsx'
import DataTable from '../DataTable.jsx'
import StatusBadge from '../StatusBadge.jsx'

export default function DenialAppealEngine({ denials, appeals }) {
  const denialColumns = [
    { key: 'id', label: 'Denial' },
    { key: 'claim_id', label: 'Claim' },
    { key: 'reason', label: 'Reason' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const appealColumns = [
    { key: 'id', label: 'Appeal' },
    { key: 'denial_id', label: 'Denial' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="section-grid">
      <div className="panel">
        <SectionHeader eyebrow="Denials" title="Denial Queue" />
        <DataTable columns={denialColumns} rows={denials} emptyState="No denials logged." />
      </div>
      <div className="panel">
        <SectionHeader eyebrow="Appeals" title="Appeal Workbench" />
        <DataTable columns={appealColumns} rows={appeals} emptyState="No appeals drafted." />
      </div>
    </div>
  )
}
