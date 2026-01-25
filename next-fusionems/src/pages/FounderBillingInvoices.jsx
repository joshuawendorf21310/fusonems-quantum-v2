import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function FounderBillingInvoices() {
  const [invoices, setInvoices] = useState([])

  useEffect(() => {
    apiFetch('/api/billing/invoices').then((data) => {
      setInvoices(Array.isArray(data) ? data : [])
    })
  }, [])

  const columns = [
    { key: 'invoice_number', label: 'Invoice' },
    { key: 'customer_id', label: 'Customer' },
    { key: 'amount_due', label: 'Amount Due', render: (row) => `$${(row.amount_due / 100).toFixed(2)}` },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Billing" title="Invoices" />
      <div className="panel">
        <DataTable columns={columns} rows={invoices} emptyState="No invoices found." />
      </div>
    </div>
  )
}
