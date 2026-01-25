import SectionHeader from '../SectionHeader.jsx'
import DataTable from '../DataTable.jsx'
import StatusBadge from '../StatusBadge.jsx'

export default function BillingSpine({ invoices }) {
  const columns = [
    { key: 'invoice_number', label: 'Invoice' },
    { key: 'customer_id', label: 'Customer' },
    { key: 'amount_due', label: 'Amount Due', render: (row) => `$${(row.amount_due / 100).toFixed(2)}` },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="panel">
      <SectionHeader eyebrow="Billing" title="Invoice Spine" />
      <DataTable columns={columns} rows={invoices} emptyState="No invoices available." />
    </div>
  )
}
