import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import {
  fallbackMedicationAdmins,
  fallbackMedicationMaster,
  fallbackFormulary,
} from '../data/fallback.js'

const masterColumns = [
  { key: 'name', label: 'Medication' },
  { key: 'drug_class', label: 'Class' },
  { key: 'concentration', label: 'Concentration' },
  { key: 'routes', label: 'Routes' },
  { key: 'status', label: 'Status' },
]

const adminColumns = [
  { key: 'medication_name', label: 'Medication' },
  { key: 'dose', label: 'Dose' },
  { key: 'dose_units', label: 'Units' },
  { key: 'route', label: 'Route' },
  { key: 'time_administered', label: 'Time' },
]

const formularyColumns = [
  { key: 'version', label: 'Version' },
  { key: 'status', label: 'Status' },
  { key: 'notes', label: 'Notes' },
]

export default function Medication() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Medication Control"
        title="Formulary + Administration"
        action={<button className="primary-button">Add Medication</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Formulary" title="Active Medication Lists" />
          <DataTable columns={formularyColumns} rows={fallbackFormulary} emptyState="No formularies." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Dose Safety"
            model="med-safety"
            version="1.9"
            level="ADVISORY"
            message="2 administrations exceeded protocol max dose; review required."
            reason="Protocol dose rules"
          />
          <div className="note-card">
            <p className="note-title">Formulary Drift</p>
            <p className="note-body">3 meds pending medical director approval.</p>
          </div>
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Master" title="Medication Catalog" />
          <DataTable columns={masterColumns} rows={fallbackMedicationMaster} emptyState="No medications." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Administration" title="Field Administrations" />
          <DataTable columns={adminColumns} rows={fallbackMedicationAdmins} emptyState="No administrations." />
        </div>
      </div>
    </div>
  )
}
