import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function FounderBillingDenials() {
  const [denials, setDenials] = useState([])

  useEffect(() => {
    apiFetch('/api/billing/denials').then((data) => {
      setDenials(Array.isArray(data) ? data : [])
    })
  }, [])

  const columns = [
    { key: 'id', label: 'Denial' },
    { key: 'claim_id', label: 'Claim' },
    { key: 'reason', label: 'Reason' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Billing" title="Denials" />
      <div className="panel">
        <DataTable columns={columns} rows={denials} emptyState="No denials logged." />
      </div>
    </div>
  )
}
