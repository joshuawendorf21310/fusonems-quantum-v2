import { useAppData } from '../context/AppContext.jsx'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'

export default function PatientCare() {
  const { patients } = useAppData()

  const columns = [
    { key: 'incident_number', label: 'Incident' },
    { key: 'first_name', label: 'First Name' },
    { key: 'last_name', label: 'Last Name' },
    {
      key: 'vitals',
      label: 'Vitals',
      render: (row) => `BP ${row.vitals?.bp || '--'} | HR ${row.vitals?.hr || '--'}`,
    },
    {
      key: 'interventions',
      label: 'Interventions',
      render: (row) => row.interventions?.join(', ') || 'None',
    },
  ]

  return (
    <div className="page">
      <SectionHeader
        eyebrow="ePCR Management"
        title="Patient Care Reporting"
        action={<button className="ghost-button">New ePCR</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <DataTable columns={columns} rows={patients} emptyState="No patient records." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Compliance" title="Documentation Quality" />
          <ul className="checklist">
            <li>96% complete vitals documentation</li>
            <li>AI prompt: add ventilator settings on critical calls</li>
            <li>HIPAA audit log enabled with encrypted storage</li>
            <li>Signature capture and QA review pending: 3 reports</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
