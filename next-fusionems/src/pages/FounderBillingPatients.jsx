import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function FounderBillingPatients() {
  const [accounts, setAccounts] = useState([])

  useEffect(() => {
    apiFetch('/api/billing/patient/accounts').then((data) => {
      setAccounts(Array.isArray(data) ? data : [])
    })
  }, [])

  const columns = [
    { key: 'patient_name', label: 'Patient' },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: 'Phone' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Billing" title="Patients" />
      <div className="panel">
        <DataTable columns={columns} rows={accounts} emptyState="No patient accounts." />
      </div>
    </div>
  )
}
