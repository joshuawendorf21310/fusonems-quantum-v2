import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function FounderBillingFacilities() {
  const [facilities, setFacilities] = useState([])

  useEffect(() => {
    apiFetch('/api/billing/facilities').then((data) => {
      setFacilities(Array.isArray(data) ? data : [])
    })
  }, [])

  const columns = [
    { key: 'name', label: 'Facility' },
    { key: 'npi', label: 'NPI' },
    { key: 'address', label: 'Address' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Billing" title="Facilities" />
      <div className="panel">
        <DataTable columns={columns} rows={facilities} emptyState="No facilities available." />
      </div>
    </div>
  )
}
