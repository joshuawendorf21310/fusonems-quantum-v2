import SectionHeader from '../SectionHeader.jsx'
import DataTable from '../DataTable.jsx'
import StatusBadge from '../StatusBadge.jsx'

export default function PatientBillingAccountsTable({ accounts }) {
  const columns = [
    { key: 'patient_name', label: 'Patient' },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: 'Phone' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="panel">
      <SectionHeader eyebrow="Patients" title="Patient Billing Accounts" />
      <DataTable columns={columns} rows={accounts} emptyState="No patient billing accounts." />
    </div>
  )
}
