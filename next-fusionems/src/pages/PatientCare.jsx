import { useAppData } from '../context/useAppData.js'
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

  const labRows = patients.flatMap((patient) =>
    (patient.labs || []).map((lab) => ({
      id: `${patient.id}-${lab.lab_type}`,
      patient: `${patient.first_name} ${patient.last_name}`,
      lab_type: lab.lab_type,
      values: Object.entries(lab.values || {})
        .map(([key, value]) => `${key}: ${value}`)
        .join(', '),
    }))
  )

  const cctRows = patients.flatMap((patient) =>
    (patient.cct_interventions || []).map((entry) => ({
      id: `${patient.id}-${entry.intervention}`,
      patient: `${patient.first_name} ${patient.last_name}`,
      intervention: entry.intervention,
      details: Object.entries(entry.details || {})
        .map(([key, value]) => `${key}: ${value}`)
        .join(', '),
    }))
  )

  const labColumns = [
    { key: 'patient', label: 'Patient' },
    { key: 'lab_type', label: 'Lab' },
    { key: 'values', label: 'Values' },
  ]

  const cctColumns = [
    { key: 'patient', label: 'Patient' },
    { key: 'intervention', label: 'Intervention' },
    { key: 'details', label: 'Details' },
  ]

  const ocrRows = patients.flatMap((patient) =>
    (patient.ocr_snapshots || []).map((snapshot, index) => ({
      id: `${patient.id}-ocr-${index}`,
      patient: `${patient.first_name} ${patient.last_name}`,
      device: snapshot.device_type || 'device',
      confidence: `${Math.round((snapshot.confidence || 0) * 100)}%`,
      status: snapshot.requires_review ? 'Review' : 'Verified',
    }))
  )

  const narrativeRows = patients.map((patient) => ({
    id: patient.id,
    patient: `${patient.first_name} ${patient.last_name}`,
    narrative: patient.narrative || 'No narrative recorded yet.',
  }))

  const ocrColumns = [
    { key: 'patient', label: 'Patient' },
    { key: 'device', label: 'Device' },
    { key: 'confidence', label: 'Confidence' },
    { key: 'status', label: 'Status' },
  ]

  const narrativeColumns = [
    { key: 'patient', label: 'Patient' },
    { key: 'narrative', label: 'Narrative' },
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
            <li>NEMSIS 3.5.1 validator active (WI ruleset loaded)</li>
            <li>OCR intake ready for monitors, vents, and IV pumps</li>
            <li>Critical care labs + interventions tracked per timeline</li>
            <li>AI narrative engine flags missing fields before finalization</li>
          </ul>
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Labs" title="CCT Lab Values" />
          <DataTable columns={labColumns} rows={labRows} emptyState="No labs recorded." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Critical Care" title="CCT Interventions" />
          <DataTable columns={cctColumns} rows={cctRows} emptyState="No CCT interventions logged." />
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="OCR" title="Device Ingest Snapshots" />
          <DataTable columns={ocrColumns} rows={ocrRows} emptyState="No OCR snapshots captured." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Narrative" title="Clinical Narrative" />
          <DataTable columns={narrativeColumns} rows={narrativeRows} emptyState="No narratives yet." />
        </div>
      </div>
    </div>
  )
}
