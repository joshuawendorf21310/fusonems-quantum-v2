import SectionHeader from '../SectionHeader.jsx'
import DataTable from '../DataTable.jsx'
import StatusBadge from '../StatusBadge.jsx'

export default function ClaimLifecycle({ claims }) {
  const columns = [
    { key: 'id', label: 'Claim' },
    { key: 'invoice_id', label: 'Invoice' },
    { key: 'payer', label: 'Payer' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="panel">
      <SectionHeader eyebrow="Claims" title="Lifecycle Tracking" />
      <DataTable columns={columns} rows={claims} emptyState="No claims in pipeline." />
    </div>
  )
}
