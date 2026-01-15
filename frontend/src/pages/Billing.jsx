import { useAppData } from '../context/AppContext.jsx'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

export default function Billing() {
  const { invoices } = useAppData()

  const columns = [
    { key: 'invoice_number', label: 'Invoice' },
    { key: 'patient_name', label: 'Patient' },
    { key: 'payer', label: 'Payer' },
    {
      key: 'amount_due',
      label: 'Amount',
      render: (row) => `$${row.amount_due.toLocaleString()}`,
    },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Billing & Business Ops"
        title="Claims, Reconciliation, and Revenue"
        action={<button className="ghost-button">Submit to Office Ally</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <DataTable columns={columns} rows={invoices} emptyState="No invoices generated." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="KPIs" title="Revenue Health" />
          <div className="stack">
            <div className="list-row">
              <div>
                <p className="list-title">Average AR Days</p>
                <p className="list-sub">24 days, improving</p>
              </div>
              <StatusBadge value="Dispatched" />
            </div>
            <div className="list-row">
              <div>
                <p className="list-title">Denied Claims</p>
                <p className="list-sub">3 in review, auto-correct suggestions ready</p>
              </div>
              <StatusBadge value="High" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
