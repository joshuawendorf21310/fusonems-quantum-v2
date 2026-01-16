import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import {
  fallbackNarcotics,
  fallbackCustody,
  fallbackDiscrepancies,
} from '../data/fallback.js'

const narcoticColumns = [
  { key: 'name', label: 'Drug' },
  { key: 'schedule', label: 'Schedule' },
  { key: 'concentration', label: 'Concentration' },
  { key: 'quantity', label: 'Qty' },
  { key: 'storage_location', label: 'Location' },
  { key: 'status', label: 'Status' },
]

const custodyColumns = [
  { key: 'event_type', label: 'Event' },
  { key: 'from_location', label: 'From' },
  { key: 'to_location', label: 'To' },
  { key: 'quantity', label: 'Qty' },
  { key: 'witness', label: 'Witness' },
]

const discrepancyColumns = [
  { key: 'summary', label: 'Issue' },
  { key: 'severity', label: 'Severity' },
  { key: 'status', label: 'Status' },
]

export default function Narcotics() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Narcotics Control"
        title="Chain of Custody + Compliance"
        action={<button className="primary-button">Log Count</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Inventory" title="Controlled Substances" />
          <DataTable columns={narcoticColumns} rows={fallbackNarcotics} emptyState="No narcotics logged." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Diversion Guard"
            model="narcotic-watch"
            version="2.2"
            level="ADVISORY"
            message="1 discrepancy requires supervisor review within 8 hours."
            reason="Chain-of-custody rules"
          />
          <div className="note-card">
            <p className="note-title">Rig Check Status</p>
            <p className="note-body">Night shift counts complete for 6 of 7 units.</p>
          </div>
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Custody" title="Transfer Timeline" />
          <DataTable columns={custodyColumns} rows={fallbackCustody} emptyState="No custody events." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Discrepancies" title="Open Flags" />
          <DataTable columns={discrepancyColumns} rows={fallbackDiscrepancies} emptyState="No discrepancies." />
        </div>
      </div>
    </div>
  )
}
