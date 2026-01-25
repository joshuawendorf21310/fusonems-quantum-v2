import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function FounderBillingClaims() {
  const [claims, setClaims] = useState([])

  useEffect(() => {
    apiFetch('/api/billing/claims').then((data) => {
      setClaims(Array.isArray(data) ? data : [])
    })
  }, [])

  const columns = [
    { key: 'id', label: 'Claim' },
    { key: 'invoice_id', label: 'Invoice' },
    { key: 'payer', label: 'Payer' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Billing" title="Claims" />
      <div className="panel">
        <DataTable columns={columns} rows={claims} emptyState="No claims submitted." />
      </div>
    </div>
  )
}
