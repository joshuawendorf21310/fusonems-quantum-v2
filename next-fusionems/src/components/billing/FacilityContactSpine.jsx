import SectionHeader from '../SectionHeader.jsx'
import DataTable from '../DataTable.jsx'
import StatusBadge from '../StatusBadge.jsx'

export default function FacilityContactSpine({ facilities, contacts }) {
  const facilityColumns = [
    { key: 'name', label: 'Facility' },
    { key: 'npi', label: 'NPI' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]
  const contactColumns = [
    { key: 'name', label: 'Contact' },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: 'Phone' },
    { key: 'role', label: 'Role' },
  ]

  return (
    <div className="section-grid">
      <div className="panel">
        <SectionHeader eyebrow="Facilities" title="Billing Facilities" />
        <DataTable columns={facilityColumns} rows={facilities} emptyState="No facilities configured." />
      </div>
      <div className="panel">
        <SectionHeader eyebrow="Contacts" title="Facility Contacts" />
        <DataTable columns={contactColumns} rows={contacts} emptyState="No contacts loaded." />
      </div>
    </div>
  )
}
